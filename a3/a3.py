# coding: utf-8

# # Assignment 3:  Recommendation systems
#
# Here we'll implement a content-based recommendation algorithm.
# It will use the list of genres for a movie as the content.
# The data come from the MovieLens project: http://grouplens.org/datasets/movielens/

# Please only use these imports.
from collections import Counter, defaultdict
import math
import numpy as np
import os
import pandas as pd
import re
from scipy.sparse import csr_matrix
import urllib.request
import zipfile

def download_data():
    """ DONE. Download and unzip data.
    """
    url = 'https://www.dropbox.com/s/h9ubx22ftdkyvd5/ml-latest-small.zip?dl=1'
    urllib.request.urlretrieve(url, 'ml-latest-small.zip')
    zfile = zipfile.ZipFile('ml-latest-small.zip')
    zfile.extractall()
    zfile.close()


def tokenize_string(my_string):
    """ DONE. You should use this in your tokenize function.
    """
    return re.findall('[\w\-]+', my_string.lower())


def tokenize(movies):
    """
    Append a new column to the movies DataFrame with header 'tokens'.
    This will contain a list of strings, one per token, extracted
    from the 'genre' field of each movie. Use the tokenize_string method above.

    Note: you may modify the movies parameter directly; no need to make
    a new copy.
    Params:
      movies...The movies DataFrame
    Returns:
      The movies DataFrame, augmented to include a new column called 'tokens'.

    >>> movies = pd.DataFrame([[123, 'Horror|Romance'], [456, 'Sci-Fi']], columns=['movieId', 'genres'])
    >>> movies = tokenize(movies)
    >>> movies['tokens'].tolist()
    [['horror', 'romance'], ['sci-fi']]
    """
    ###TODO
    tokens=[]
    for token in movies['genres']:
       v = tokenize_string(token)
       tokens.append(v)
    movies['tokens']=tokens
    return movies


def featurize(movies):
    """
    Append a new column to the movies DataFrame with header 'features'.
    Each row will contain a csr_matrix of shape (1, num_features). Each
    entry in this matrix will contain the tf-idf value of the term, as
    defined in class:
    tfidf(i, d) := tf(i, d) / max_k tf(k, d) * log10(N/df(i))
    where:
    i is a term
    d is a document (movie)
    tf(i, d) is the frequency of term i in document d
    max_k tf(k, d) is the maximum frequency of any term in document d
    N is the number of documents (movies)
    df(i) is the number of unique documents containing term i

    Params:
      movies...The movies DataFrame
    Returns:
      A tuple containing:
      - The movies DataFrame, which has been modified to include a column named 'features'.
      - The vocab, a dict from term to int. Make sure the vocab is sorted alphabetically as in a2 (e.g., {'aardvark': 0, 'boy': 1, ...})
    """
    ###TODO
    unsortedvocab = defaultdict(int)
    features = movies['tokens'].tolist()
    max_k = {}
    vocab =defaultdict(int) 
    tf = defaultdict(int)
    df = defaultdict(int)
    tfidf = {}
    num_features=[]
    csr_matrixlist= [] 
    doc = 0
    document = 0
    for values in features:
        max_k[document]=0
        for value in values:
            num_features.append(value)
            if (value,document) not in tf:
                df[value]+=1
            tf[(value,document)]+=1
        max_k[document]=np.max(tf[value,document])
        document+=1
        
    documentcount = len(features)
    for val in sorted(set(num_features)):
        vocab[val]=len(vocab)
    for values in features:
        indptr = []
        indices = []
        data = []
        for value in values:
            if value in vocab:
                tfidf[(value,doc)] = (tf[(value,doc)]/max_k[doc]) * math.log10(documentcount/df[value])
                data.append(tfidf[(value,doc)])
                indptr.append(0)
                indices.append(vocab[value])
        matrix=csr_matrix((data, (indptr, indices)),shape = (1,len(vocab)))
        csr_matrixlist.append(matrix)
        doc+=1
    movies['features'] = csr_matrixlist
    return tuple((movies,vocab))


def train_test_split(ratings):
    """DONE.
    Returns a random split of the ratings matrix into a training and testing set.
    """
    test = set(range(len(ratings))[::1000])
    train = sorted(set(range(len(ratings))) - test)
    test = sorted(test)
    return ratings.iloc[train], ratings.iloc[test]


def cosine_sim(a, b):
    """
    Compute the cosine similarity between two 1-d csr_matrices.
    Each matrix represents the tf-idf feature vector of a movie.
    Params:
      a...A csr_matrix with shape (1, number_features)
      b...A csr_matrix with shape (1, number_features)
    Returns:
      The cosine similarity, defined as: dot(a, b) / ||a|| * ||b||
      where ||a|| indicates the Euclidean norm (aka L2 norm) of vector a.
    """
    ###TODO
    dotproduct = np.dot(a,np.transpose(b))
    normalise = np.linalg.norm(a.toarray())*np.linalg.norm(b.toarray())
    return (dotproduct/normalise).data


def make_predictions(movies, ratings_train, ratings_test):
    """
    Using the ratings in ratings_train, predict the ratings for each
    row in ratings_test.

    To predict the rating of user u for movie i: Compute the weighted average
    rating for every other movie that u has rated.  Restrict this weighted
    average to movies that have a positive cosine similarity with movie
    i. The weight for movie m corresponds to the cosine similarity between m
    and i.

    If there are no other movies with positive cosine similarity to use in the
    prediction, use the mean rating of the target user in ratings_train as the
    prediction.

    Params:
      movies..........The movies DataFrame.
      ratings_train...The subset of ratings used for making predictions. These are the "historical" data.
      ratings_test....The subset of ratings that need to predicted. These are the "future" data.
    Returns:
      A numpy array containing one predicted rating for each element of ratings_test.
    """
    ###TODO
    listedrating = []
    for index,rows in ratings_test.iterrows():
        total = 0
        totalcount=0
        flag=0
        ratingcol = []
        test_movie = rows['movieId']
        test_user = rows['userId']
        data = movies.loc[movies['movieId']==int(test_movie)]
        a = data['features'].values[0]
        df = ratings_train.loc[(ratings_train['userId']==int(test_user)) &(ratings_train['movieId']!=test_movie)]
        for ind,row in df.iterrows():
                ratingcol.append(row['rating'])
                train_data = movies.loc[movies['movieId']==int(row['movieId'])]
                b = train_data['features'].values[0]
                cosineval = cosine_sim(a,b)
                if cosineval>0:
                    total+=cosineval
                    totalcount+=(cosineval*row['rating'])
        if total>0:
            listedrating.append(totalcount/total)
        else:
            listedrating.append(np.mean(ratingcol))
    return (listedrating)


def mean_absolute_error(predictions, ratings_test):
    """DONE.
    Return the mean absolute error of the predictions.
    """
    return np.abs(predictions - np.array(ratings_test.rating)).mean()


def main():
    download_data()
    path = 'ml-latest-small'
    ratings = pd.read_csv(path + os.path.sep + 'ratings.csv')
    movies = pd.read_csv(path + os.path.sep + 'movies.csv')
    movies = tokenize(movies)
    movies, vocab = featurize(movies)
    print('vocab:')
    print(sorted(vocab.items())[:10])
    ratings_train, ratings_test = train_test_split(ratings)
    print('%d training ratings; %d testing ratings' % (len(ratings_train), len(ratings_test)))
    predictions = make_predictions(movies, ratings_train, ratings_test)
    print('error=%f' % mean_absolute_error(predictions, ratings_test))
    print(predictions[:10])


if __name__ == '__main__':
    main()
