# Pixabay Data Analysis

During the analysis of possible obstacles to the Pixabay data analysis, a limitation in the use of the API of ***100 requests per minute*** and the ability to view only ***500 (600)** results* according to the specified parameters was mainly determined.

Accordingly, to collect ***4000* *images***, it is necessary to make ***8 (7) requests*** and get unique images. To meet these requirements, several options were considered: use different search queries, use categories as parameters, use colors as parameters. Due to the low number of images that were in several categories at once, it was decided to use **colors** in the parameters.

However, such an approach can generate disproportionate saving of images with certain parameters. To solve this problem, it was decided to calculate the proportions for each color:

```python
def calculate_proportional_images(cls, color_data, total, total_images):
        proportions = {color: count / total for color, count in color_data.items()}
        logger.info(f'Got proportions {proportions}')
        return {color: round(proportion * total_images) for color, proportion in proportions.items()}
```

It was also necessary to ensure the uniqueness of the images in the sample. Given the limit on the number of requests and results, it was decided to use additional variables in the parameters

```python
params = {
                    'key': self.api_key,
                    'colors': color,
                    'image_type': 'all' if attempts == 1 else image_type[attempts % len(image_type)],
                    'per_page': 200,
                    'page': page,
                    'editors_choice': 'true' if attempts == 4 else 'false',
                    'languages': 'en' if attempts < 5 else languages[attempts % len(languages)],
                }
```

Some images can be re-selected when applying different parameters, also, you need to follow the necessary proportions in the sample, for this the following function was implemented:

```python
async def remove_duplicates(cls, api, session, df, prop):
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
```

Taking into account the fact that in tags some words can have a similar meaning but different forms, a function was created to lemmatize tags:

```python
def lemmatize_tags(cls, df, column_name):
        lemmatizer = WordNetLemmatizer()
        df[column_name] = df[column_name].apply(lambda x: ' '.join([lemmatizer.lemmatize(word) for word in word_tokenize(x)]))
        return df
```

To organize the storage of the received data in a structured form, 4 tables were created: image_facts, image_types, tags, users.

#### image_facts table

| Column Name   | **Type** | Relations           |
| ------------- | -------------- | ------------------- |
| id            | Integer        |                     |
| user_id       | Integer        | users.user_id       |
| type_id       | Integer        | image_types.type_id |
| tag1_id       | Integer        | tags.tag_id         |
| tag2_id       | Integer        | tags.tag_id         |
| tag3_id       | Integer        | tags.tag_id         |
| views         | Integer        |                     |
| downloads     | Integer        |                     |
| collections   | Integer        |                     |
| likes         | Integer        |                     |
| comments      | Integer        |                     |
| imageWidth    | Integer        |                     |
| imageSize     | Integer        |                     |
| largeImageURL | String         |                     |
| pageURL       | String         |                     |
| created_at    | DateTime       |                     |

#### image_types

| Column Name | Type    | Relations           |
| ----------- | ------- | ------------------- |
| type_id     | Integer | image_facts.type_id |
| type        | String  |                     |

#### tags

| Column Name | Type    | Relations                                                             |
| ----------- | ------- | --------------------------------------------------------------------- |
| tag_id      | Integer | image_facts.tag1_id<br />image_facts.tag2_id<br />image_facts.tag3_id |
| tag         | String  |                                                                       |

#### users

| Column Name  | Type    | Relations           |
| ------------ | ------- | ------------------- |
| user_id      | Integer | image_facts.user_id |
| user         | String  |                     |
| userImageURL | String  |                     |

For a complete and thorough analysis of data from images from Pixabay, the following visualizations were created:

1. Linear regression visualizations Comments vs Likes and Views vs Downloads
2. Charts with the top 10 tags for likes, downloads count and tag-pairs
3. Chart with Distribution of likes
4. Analytical table with user data and views, downloads, likes, comments, total images
