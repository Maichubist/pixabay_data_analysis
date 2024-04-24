import pandas as pd
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import asyncio

from extractor import PixabayAPI, ClientSessionManager
from logging_config import logger
from db_interaction import db

##Uncomment while first use
# nltk.download('wordnet')
# nltk.download('omw-1.4')

class Processor:
    """
    A class for processing image data from Pixabay API and handling data transformations.
    """

    @classmethod
    async def get_dataset(cls, session, colors_list, total_required, api):
        """
        Asynchronously gather and process a dataset of images based on color proportions.

        Args:
            session (ClientSession): The aiohttp session to use for HTTP requests.
            colors_list (list): List of colors to gather images for.
            total_required (int): Total number of images required.
            api (PixabayAPI): The Pixabay API client instance.

        Returns:
            pd.DataFrame: A DataFrame containing the processed image data.
        """
        color_data, total = await api.gather_color_data(session, colors_list)
        color_proportions = cls.calculate_proportional_images(color_data, total, total_required)
        images_data = await api.collect_images(session, color_proportions)
        df = pd.DataFrame([image for sublist in images_data for image in sublist])
        df = cls.lemmatize_tags(df, 'tags')
        att = 0
        while len(df) != total_required and att < 3:
            logger.info(f'Attempt {att} to update df')
            df = await cls.remove_duplicates(api, session, df, color_proportions)
            att+=1
        return df
    

    @classmethod
    async def remove_duplicates(cls, api, session, df, prop):
        """
        Remove duplicates from the DataFrame based on image IDs and adjust counts per color.

        Args:
            api (PixabayAPI): The Pixabay API client instance.
            session (ClientSession): The aiohttp session to use for HTTP requests.
            df (pd.DataFrame): DataFrame containing image data.
            prop (dict): Dictionary containing the target number of images per color.

        Returns:
            pd.DataFrame: The DataFrame after removing duplicates and adjusting the counts.
        """
        df.drop_duplicates(subset='id', inplace=True)
        value_counts = df['color'].value_counts()
        for color, planned_number in prop.items():
            overrun = value_counts[color] - planned_number
            if color in value_counts and overrun > 0:
                indices_to_drop = np.random.choice(df[df['color'] == color].index, size=overrun, replace=False)
                df = df.drop(indices_to_drop)
                logger.info(f"Removed {value_counts[color] - planned_number} duplicates from {color}.")

            elif color in value_counts and overrun < 0:
                for i in range(3, 9):
                    additional_images = await api.fetch_color_images(session, color, planned_number-value_counts[color], i)
                    df = pd.concat([df, pd.DataFrame(additional_images)], ignore_index=True)
                    logger.info(f"Added {len(additional_images)} new images for {color} to replace duplicates.")
        return df

    @classmethod
    def calculate_proportional_images(cls, color_data, total, total_images):
        """
        Calculate the proportional amount of images needed per color based on total images required.

        Args:
            color_data (dict): Dictionary containing color data with total counts.
            total (int): Total number of images across all colors.
            total_images (int): Total number of images required.

        Returns:
            dict: A dictionary mapping each color to the proportional number of images required.
        """
        proportions = {color: count / total for color, count in color_data.items()}
        logger.info(f'Got proportions {proportions}')
        return {color: round(proportion * total_images) for color, proportion in proportions.items()}
    
    @classmethod
    def lemmatize_tags(cls, df, column_name):
        """
        Lemmatize the tags in the DataFrame to unify similar words to their base form.

        Args:
            df (pd.DataFrame): The DataFrame containing image tags.
            column_name (str): The column name in the DataFrame that contains tags.

        Returns:
            pd.DataFrame: The DataFrame with lemmatized tags.
        """
        lemmatizer = WordNetLemmatizer()
        df[column_name] = df[column_name].apply(lambda x: ' '.join([lemmatizer.lemmatize(word) for word in word_tokenize(x)]))
        return df


async def main():
    """
    Main asynchronous function to gather and process image data and upload to a database.
    """
    try:
        api = PixabayAPI('your_api_key_here')
        processor = Processor()
        colors_list = ["grayscale", "transparent", "red", "orange", "yellow", "green", "turquoise", "blue", "lilac", "pink", "white", "gray", "black", "brown"]
        async with ClientSessionManager() as session:
            logger.info('Collecting and processing started')
            final_data = await processor.get_dataset(session, colors_list, 4000, api)
            logger.info('Dataset created, load to DB started')
            db.load_data_to_db(final_data)
            logger.info('Load to DB finished')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())