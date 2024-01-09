import pandas as pd
import numpy as np

class RetrievalSystem:

    def retrieve(collection : pd.DataFrame, users_embeddings : list[list[float]], num_results = 10):
        """
        returns the json list of the top k suggested news
        """

        if users_embeddings is None or len(users_embeddings) == 0:
            return collection.head(num_results).to_json(orient="records")

        return RetrievalSystem.__retrieve_mean(collection, users_embeddings, num_results)

    def __retrieve_mean(collection : pd.DataFrame, users_embeddings : list[list[float]], num_results = 10):
        """
        returns the json list of the top k suggested news
        according to the highest dot product between each news and the mean of the representation of the users
        """
        # each row of the collection is a news, each news has 
        # an attribute 'Embedding'

        # each element of the list of users_embeddings contains an embedding associated with an user

        users_mean = np.mean( np.array(users_embeddings), axis=0 )

        def func(row): 
            ret = 0
            for (idx, emb) in enumerate(row['Embedding']):
                ret += (emb * users_mean[idx])
            return ret
        
        collection['score'] = collection.apply(func, axis=1 )

        print(f"collection columns: {collection.columns}")
        print(f"df[:10]{collection['score'].head(10).to_list()}")

        collection.sort_values('score', ascending=False, inplace=True)
        return collection.head(num_results).to_json(orient="records")