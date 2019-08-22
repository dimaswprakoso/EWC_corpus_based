import mysql.connector
import datetime
import math

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import brown
# from nltk.corpus import reuters



# ----------------------------------------------------------------------------#
# Configuration
# ----------------------------------------------------------------------------#
starttime = datetime.datetime.now()
print("start:%s" % starttime)

db_user = 'root'
db_database = 'sharebox'
language = 'EN'

# testing---------#
base_word = 'stem' # raw, stem, lemma
# ----------------#

db_table = "ic_%s" % (base_word)


# ----------------------------------------------------------------------------#
# 0. Initialize
# ----------------------------------------------------------------------------#
# Mysql Connection
cnx = mysql.connector.connect(user=db_user, database=db_database)
cursor = cnx.cursor(dictionary=True)

# ----------------------------------------------------------------------------#
# 1. Get items from workshop
# ----------------------------------------------------------------------------#
sql = """
SELECT * FROM `workshop_items2` WHERE language = '""" + language + """' AND type='Material' 
"""

item_list = {}
try:
    results = cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        item_list[row['id']] = [row['Waste_description'], row['Wastecode']]

    print("Items rows: {}".format(cursor.rowcount))

except mysql.connector.Error as e:
    print("x Failed loading data: {}\n".format(e))

# ----------------------------------------------------------------------------#
# 2. Get items from ewc
# ----------------------------------------------------------------------------#
sql = """
SELECT * FROM `ewc_level3`
"""

ewc_list = {}

try:
    results = cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        ewc_list[row['EWC_level3']] = [row['description'], row['id']]

    print("EWC rows: {}".format(cursor.rowcount))

except mysql.connector.Error as e:
    print("x Failed loading data: {}\n".format(e))

# ----------------------------------------------------------------------------#
# 3. Empty table word similarity
# ----------------------------------------------------------------------------#
sql = "TRUNCATE TABLE %s" % db_table

try:
    cursor.execute(sql)

except mysql.connector.Error as e:
    print("x Failed inserting data: {}\n".format(e))


# ----------------------------------------------------------------------------#
# preprocessing
# ----------------------------------------------------------------------------#
def NLP(data):
    # 0. Lowercase
    data = data.lower()

    # 1. Tokenize # word tokenize (removes also punctuation)
    tokenizer = RegexpTokenizer(r'[a-zA-Z_]+')
    words = tokenizer.tokenize(data)

    # 2. Remove short words
    words = [w for w in words if len(w) > 2]

    # 3. Remove Stopwords # load stopwords from enlgihs language
    stop_words = set(stopwords.words("english"))
    words = [w for w in words if not w in stop_words]  # for each word check if

    # 4 Remove common terminology in waste listings e.g. (waste)
    term_list = ['waste', 'scrap', 'scraps', 'process', 'processes', 'processed', 'processing', 'unprocessed',
                 'consultancy', 'advice', 'training', 'service', 'managing', 'management', 'recycling', 'recycle',
                 'industry', 'industrial', 'material', 'materials', 'quantity', 'support', 'residue', 'organic',
                 'remainder', 'specific', 'particular', 'solution', 'solutions', 'substance', 'substances', 'product',
                 'production', 'use', 'used', 'unused', 'consumption', 'otherwise', 'specified', 'based', 'spent',
                 'hazardous', 'dangerous','containing','other']

    words = [w for w in words if not w in term_list]  # for each word check if
    data = words

    # 5. Find Stem # Porter Stemmer

    if base_word=='stem':
        ps = PorterStemmer()
        stemmed_words = []
        for w in words:
            stemmed_words.append(ps.stem(w))
        data = stemmed_words
    elif base_word=='lemma':
        lm = WordNetLemmatizer()
        lemmatized_words = []
        for w in words:
            lemmatized_words.append(lm.lemmatize(w))
        data = lemmatized_words

    return data


# ----------------------------------------------------------------------------#
# information content Functions
# ----------------------------------------------------------------------------#
def info_content(lookup_word): # for Li's sentence similarity
    """
    Uses the Brown corpus available in NLTK to calculate a Laplace
    smoothed frequency distribution of words, then uses this information
    to compute the information content of the lookup_word.
    """
    N = 0
    if N == 0:
        # poor man's lazy evaluation
        for sent in brown.sents():
            for word in sent:
                word = word.lower()
                if word not in brown_freqs:
                    brown_freqs[word] = 0
                brown_freqs[word] = brown_freqs[word] + 1
                N = N + 1
    lookup_word = lookup_word.lower()
    n = 0 if lookup_word not in brown_freqs else brown_freqs[lookup_word]

    return 1.0 - (math.log(n + 1) / math.log(N + 1))


# ----------------------------------------------------------------------------#
# Main code
# ----------------------------------------------------------------------------#
# --------------- Config -------------------- #
ewc_words = {}  # bag of words from the ewc description
item_words = {}  # bag of words from the item description
all_unique_words = []
brown_freqs = dict()
# reuters_freqs = dict()
ic_rows = []
# --------------- End Config ---------------- #

# Prepare the item_desc
for i, j in item_list.items():
    # clean EWC data
    item_ewc = j[1].strip()

    # delete * symbol from ewc code
    # translation_table = dict.fromkeys(map(ord, '*'), None)
    # item_ewc = item_ewc.translate(translation_table)
    item_list[i] = [j[0], item_ewc.strip()]

    desc = j[0].strip()

    # Generate word list for each waste description
    item_words[i] = NLP(desc)

    all_unique_words = list(set(all_unique_words + item_words[i]))

# prepare the ewc_desc
for k, l in ewc_list.items():
    ewc_words[k] = NLP(l[0])
    all_unique_words = list(set(all_unique_words + ewc_words[k]))


# build word similarity and information content cache
print("unique words: {}".format(len(all_unique_words)))

for first_word in all_unique_words:
    ic_row = (first_word, info_content(first_word))
    ic_rows.append(ic_row)

sql = """INSERT INTO """ + db_table + """(word1, ic) VALUES (%s, %s)"""

try:
    cursor.executemany(sql, ic_rows)
    cnx.commit()
except mysql.connector.Error as e:
    print("x Failed inserting data: {}\n".format(e))

endtime = datetime.datetime.now()
print("start  :%s" % starttime)
print("end    :%s" % endtime)
print("elapsed:%s" % (endtime - starttime))
