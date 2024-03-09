from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import re
import pandas as pd
import sqlite3

app = Flask(__name__)
app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1,0,0'),
    'description': LazyString(lambda: 'Documentation API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config ={
    "headers":[],
    "specs":[
        {
            "endpoint":'docs',
            "route":'/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,
                  config=swagger_config)

#equation cleantext
def cleantext(teks):
    teks = teks.lower()
    teks = re.sub("http\S+","", teks)
    teks = re.sub("www\S+","",teks)
    teks = re.sub("\n"," ", teks)
    teks = re.sub("\n\S+"," ", teks)
    teks = re.sub("x\S+" ,"", teks)
    teks = re.sub(r"[^a-zA-Z0-9]"," ", teks)
    teks = re.sub(" +", " ", teks)
    teks = teks.strip()
    return teks

#equation cleanstop
factory = StopWordRemoverFactory()
list_stopword = factory.get_stop_words()
katabaru = ['pengguna', 'rt pengguna', 'rt','orang','kamu','aku','uniform resource locator','uniform resource', 'resource locator','uniform','resource','locator']
list_stopword = list_stopword + katabaru
stopword = factory.create_stop_word_remover()
def cleanstop (teks):
    listkata =[]
    for x in teks.split():
        if x in list_stopword:
            stopword.remove(x)
        else:
            x = x
            listkata.append(x)
            
    kalimat = ' '.join(listkata)
    return kalimat

#equation cleanalay
kamusalay = pd.read_csv("new_kamusalay.csv",encoding='latin-1')
kamus2 = kamusalay.set_index('anakjakartaasikasik')['anak jakarta asyik asyik'].to_dict()
def cleanalay (teks):
    listkata =[]
    for kata in teks.split():
        if kata in kamus2:
            kata = kamus2[kata]
            listkata.append(kata)
        else:
            kata = kata
            listkata.append(kata)
            
    kalimat = ' '.join(listkata)
    return kalimat

#clean total
def cleantotal (teks):
    tekss = cleantext(teks)
    tekss = cleanalay(tekss)
    tekss = cleanstop(tekss)
    return tekss

#connect database sebelum atau sesudah endpoint?
conn = sqlite3.connect('data-cleansing-putri.db')
conn.execute('''CREATE TABLE tabelteks (teksinput varchar(255), teksclean varchar(255))''')
conn.execute('''CREATE TABLE tabelfile (fileinput varchar(255), fileclean varchar(255))''')
conn.close()

#endpoint hello
@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/',methods=['GET'])
def hello():
    json_response ={
        'status code': 200,
        'description': "Selamat Datang di API Cleansing Putri Oktaviani!!! Jangan lupa tambahkan 'docs' di link!",
        'data':"Challenge Gold BINAR DSC"
    }
    response_data = jsonify(json_response)
    return response_data

#endpoint input text
@swag_from("docs/text_processing.yml",methods=['POST'])
@app.route('/Masukan-Kata-Kalimat', methods=['POST'])
def text_processing():
    text = request.form.get('text')
    text = re.sub(r'\\n',' ', text)

    #connect database
    conn = sqlite3.connect('data-cleansing-putri.db')
    cursor = conn.cursor()
    
    #cleansing
    data = cleantotal(text)

    #insert text
    insert = "INSERT INTO tabelteks (teksinput, teksclean) VALUES (?, ?)"
    val = (text, data)
    cursor.execute(insert, val)
    conn.commit()
    conn.close()

    json_response = {
        'description': "Teks yang sudah diproses",
        'data': data,
    }

    response_data= jsonify(json_response)
    return response_data

#endpoint inputfile
@swag_from("docs/text_processing_file.yml",methods=['POST'])
@app.route('/Masukan-File-Text', methods=['POST'])
def text_processing_file():
    file = request.files.getlist('file')[0]
    df = pd.read_csv(file, encoding='latin-1')
    df['Tweet'] = df['Tweet'].replace(r'\\n',' ',regex=True)
    texts = df.Tweet.tolist()

    #connect database(?)
    conn = sqlite3.connect('data-cleansing-putri.db')
    cursor = conn.cursor()

    #cleansing
    data = []
    for x in texts:
        data.append(cleantotal(x))

    #insert file
    for i in range(0,len(texts)):
        insert = "INSERT INTO tabelfile (fileinput, fileclean) VALUES (?, ?)"
        val = (texts[i], data[i])
        cursor.execute(insert, val)
        conn.commit()
        
    conn.close()

    json_response = {
        'description': "Teks yang sudah diproses",
        'data': data,
    }

    response_data= jsonify(json_response)
    return response_data

if __name__ == '__main__':
    app.run()