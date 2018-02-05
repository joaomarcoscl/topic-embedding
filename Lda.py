from gensim import corpora, models
from scipy.spatial.distance import cosine, euclidean
import numpy as np
import operator
import pickle


class Lda(object):
	def __init__(self, process, tfidf, w2v, num_topics, p, limit_labels):
		self.process = process
		self.tfidf = tfidf
		self.w2v = w2v
		self.num_topics = num_topics
		self.p = p
		self.limit_labels = limit_labels
		self.texts = self.process.data[self.process.dataset]['corpus'][:int(len(self.process.data[self.process.dataset]['corpus'])*self.p)]
		self.texts_test = self.process.data[self.process.dataset]['corpus'][int(len(self.process.data[self.process.dataset]['corpus'])*self.p):]
		self.targets = self.process.data[self.process.dataset]['targets']

	def topic_tfidf(self):
		self.dictionary = corpora.Dictionary(self.texts)
		corpus = [self.dictionary.doc2bow(text) for text in self.texts]
		self.lda_model = models.ldamodel.LdaModel(corpus=corpus, id2word=self.dictionary, num_topics=self.num_topics, update_every=1, chunksize=10000, passes=1)

	def train(self):
		data_clusters_tfidf = {} 
		data_clusters_labels = {}
		data_clusters_w2v = {}
		self.train_data = {}

		for i in range(int(len(self.texts))):
			topic = sorted(dict(self.lda_model.get_document_topics(self.dictionary.doc2bow(self.texts[i]))).items(),  key=operator.itemgetter(1),reverse=True)[0][0]
			if topic not in data_clusters_tfidf:
				data_clusters_tfidf[topic] = []
				data_clusters_labels[topic] = []
				data_clusters_w2v[topic] = []
			data_clusters_tfidf[topic].append(self.tfidf.tfidf[i].toarray())
			data_clusters_labels[topic].append(self.targets[i])
			data_clusters_w2v[topic].append(self.w2v.w2v[i])

		for i in data_clusters_tfidf:
			topic = {}
			labels_topic = []
			for j in set(data_clusters_labels[i]):
				topic[j] = data_clusters_labels[i].count(j)
			[labels_topic.append(j[0]) for j in sorted(topic.items(),key=operator.itemgetter(1),reverse=True)[:self.limit_labels]]
			self.train_data[i] = {
				'labels':labels_topic, 
				'tfidf':np.mean(np.asarray(data_clusters_tfidf[i]), axis=0),
				'w2v':np.mean(np.asarray(data_clusters_w2v[i]), axis=0), 
				'terms':self.lda_model.get_topic_terms(i)
			}
		pickle.dump(self.train_data, open('data/train_'+self.process.dataset+'.ipy', 'wb'), pickle.HIGHEST_PROTOCOL)	

	def load(self):
		self.train_data = pickle.load(open('data/train_'+self.process.dataset+'.ipy', 'rb'))

	def test(self):
		a = 0
		for i in range(int(len(self.texts_test))):
			dist = {}
			somas = {}
			tfidf = self.tfidf.tfidf[i].toarray()[0]
			for j in self.train_data:
				soma = 0
				dist[j] = cosine(tfidf, self.train_data[j]['tfidf'])
				#dist[j] = cosine(w2v[i], self.train_data[j]['w2v'])
				for x in self.train_data[j]['terms']:
					soma+= (tfidf[x[0]]*x[1])
				somas[j] = soma
			#topic = sorted(somas.items(), key=operator.itemgetter(1), reverse=True)[0][0]
			topic = sorted(dist.items(), key=operator.itemgetter(1), reverse=True)[0][0]
			if self.targets[i] in self.train_data[topic]['labels']:
				a+=1
		print a, int(len(self.texts_test))