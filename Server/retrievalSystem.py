import pandas as pd
import numpy as np
import os

RETRIEVE_METHOD = os.getenv("RETRIEVE_METHOD")

class RetrievalSystem:

    def retrieve(collection : pd.DataFrame, users_embeddings : list[list[float]], num_results = 10):
        """
        returns the json list of the top k suggested news
        """

        if users_embeddings is None or len(users_embeddings) == 0:
            return collection.head(num_results).to_json(orient="records")

        if RETRIEVE_METHOD == "BY_CENTROIDS":
            return RetrievalSystem.__retrieve_centroid(collection, users_embeddings, num_results)
        else:
            #RetrievalSystem.__retrieve_centroid(collection, users_embeddings, num_results)
            return RetrievalSystem.__retrieve_scores_avg(collection, users_embeddings, num_results)

    def __retrieve_centroid(collection : pd.DataFrame, users_embeddings : list[list[float]], num_results = 10):
        """
        returns the json list of the top k suggested news
        according to the highest dot product between each news and the centroid of the representation of the users
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
        collection.sort_values('score', ascending=False, inplace=True)
        
        print(f"[__retrieve_centroid] collection columns: {collection.columns}")
        print(f"[__retrieve_centroid] df[:10]{collection['score'].head(10).to_list()}")

        return collection.head(num_results).to_json(orient="records")
    
    def __retrieve_scores_avg(collection : pd.DataFrame, users_embeddings : list[list[float]], num_results = 10):
        """
        returns the json list of the top k suggested news
        according to the highest average of the dot products between each news and each representation of the users
        """
        # each row of the collection is a news, each news has 
        # an attribute 'Embedding'

        # each element of the list of users_embeddings contains an embedding associated with an user

        def func(row, user_embedding): 
            ret = 0
            for (idx, emb) in enumerate(row['Embedding']):
                ret += (emb * user_embedding[idx])
            return ret
        
        scores_series = []
        
        for user_emb in users_embeddings:
            scores_series.append( collection.apply(func, args=[user_emb], axis=1 ) )

        # Compute the mean along the specified axis (axis=0 for column-wise mean)
        tmp = np.array(scores_series)
        #print("tmp.shape: ", tmp.shape)
        result_series = np.mean(tmp, axis=0)

        #print(f"len(result_series): ", len(result_series), "how many scores_series: ", len(scores_series))

        collection['score'] = result_series
        collection.sort_values('score', ascending=False, inplace=True)
        
        print(f"[__retrieve_scores_avg] collection columns: {collection.columns}")
        print(f"[__retrieve_scores_avg] df[:10]{collection['score'].head(10).to_list()}")

        return collection.head(num_results).to_json(orient="records")