import asyncio
import aiohttp

from logging_config import logger


class ClientSessionManager:
    """Manage the asynchronous HTTP client session."""
    async def __aenter__(self):
        """Start an asynchronous context manager, initializing the session."""
        self.session = aiohttp.ClientSession()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the asynchronous context manager, closing the session."""
        await self.session.close()

class PixabayAPI:
    """A client for fetching image data from the Pixabay API."""
    def __init__(self, key):
        self.api_key = key
        self.base_url = 'https://pixabay.com/api/'
    
    async def fetch(self, session, params):
        """Asynchronously fetch data from Pixabay API based on the given parameters.
        
        Args:
        session (aiohttp.ClientSession): The session used to make HTTP requests.
        params (dict): The parameters for the API request.
        
        Returns:
        dict or None: The JSON response parsed into a dictionary if the request is successful, otherwise None.
        """
        url = self.base_url
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"Client error {e.status} for URL {url}: {e.message}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client exception for URL {url}: {str(e)}")
            return None

    async def gather_color_data(self, session, colors):
        """Gather color-specific image data from Pixabay.
        
        Args:
        session (aiohttp.ClientSession): The session to use for requests.
        colors (list): A list of color strings to gather data for.
        
        Returns:
        tuple: A tuple containing a dictionary of color data and the total count of images across all colors.
        """
        color_data = {}
        tasks = []
        total = 0
        for color in colors:
            params = {'key': self.api_key, 'colors': color, 'image_type': 'photo', 'per_page': 3}
            task = asyncio.create_task(self.fetch(session, params))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        for result, color in zip(results, colors):
            if result:
                color_data[color] = result['total']
                total+=result['total']
        logger.info(f'Got color data {color_data} for total number: {total}')
        return color_data, total
    
    async def fetch_color_images(self, session, color, total_required, attempts=0):
        """Fetch images of a specific color until the required number is met, adapting strategy based on attempts.
        
        Args:
        session (aiohttp.ClientSession): The session to use for requests.
        color (str): The color filter for the images.
        total_required (int): The total number of unique images required.
        attempts (int): The number of attempts made to fetch the images (used internally to adapt request parameters).
        
        Returns:
        list: A list of unique images that match the color criteria.
        """
        collected_images = []
        unique_ids = set()
        max_attempts = 9
        image_type = ["photo", "illustration", "vector"]
        languages = ['ja','ru', 'de', 'fr', 'es']

        while len(unique_ids) < total_required and attempts < max_attempts:
            for page in range(1, 4): 
                params = {
                    'key': self.api_key,
                    'colors': color,
                    'image_type': 'all' if attempts == 1 else image_type[attempts % len(image_type)],
                    'per_page': 200,
                    'page': page,
                    'editors_choice': 'true' if attempts == 4 else 'false',
                    'languages': 'en' if attempts < 5 else languages[attempts % len(languages)],
                }
                data = await self.fetch(session, params)
                if data and 'hits' in data:
                    new_images = []
                    for img in data['hits']:
                        if img['id'] not in unique_ids:
                            img['color'] = color 
                            img['image_type'] = params['image_type']
                            img['editors_choice'] = params['editors_choice']
                            img['languages'] = params['languages']
                            new_images.append(img)
                            unique_ids.add(img['id'])

                    collected_images.extend(new_images)
                    logger.info(f"Fetched {len(new_images)} new images for {color} on page {page}, attempt {attempts + 1}")

                    if len(unique_ids) >= total_required:
                        break
            attempts += 1
        return collected_images
    
    async def collect_images(self, session, color_proportions):
        """Collect images based on specified color proportions asynchronously.
        
        Args:
        session (aiohttp.ClientSession): The session to use for requests.
        color_proportions (dict): A dictionary mapping colors to the proportion of images required for each.
        
        Returns:
        list: A list of gathered tasks representing the image fetching operations.
        """
        tasks = []
        for color, proportion in color_proportions.items():
            task = asyncio.create_task(self.fetch_color_images(session, color, proportion))
            tasks.append(task)
        return await asyncio.gather(*[t for t in tasks])


