import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, request, render_template
import joblib
import mysql.connector
import os

app = Flask(__name__)
model = joblib.load(open('model.pkl', 'rb'))
cv = joblib.load(open('cv.pkl', 'rb'))

myDb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='capstone'
)

if (myDb.is_connected()):
    print('connected!')
else:
    print('not connected')
    
def fetchAndUpdateAnalytics():
    if os.path.exists('static/sentiments.png'):
        os.remove('static/sentiments.png')

    mycursor = myDb.cursor()
    mycursor.execute("SELECT * FROM reviews")    
    myresult = mycursor.fetchall()

    mycursor.close()

    positive = []
    negative = []

    for row in myresult:
        if row[2] < 3:
            negative.append(row[2])
        else:
            positive.append(row[2])

    y = np.array([len(positive), len(negative)])
    mylabels = ["Positive", "Negative"]
    
    explode = (0.1, 0.0)

    plt.close()

    plt.pie(y, labels = mylabels, autopct='%1.1f%%', colors=["#5dbb63", "tomato"], shadow = True, explode = explode)
    plt.legend(title = "Customer's Sentiments : -")
    plt.savefig('static/sentiments.png')
    plt.switch_backend('agg')
    
    return myresult

@app.route('/')
def home():
    myresult = fetchAndUpdateAnalytics()
    return render_template('index.html', myresult=myresult)


@app.route('/predict', methods=['POST'])
def predict():
    '''
    For rendering results on HTML GUI
    '''

    if request.method == 'POST':
        text = request.form['review']
        stars = request.form['rating_input']
        data = [text]
        vectorizer = cv.transform(data).toarray()
        prediction = model.predict(vectorizer)
        print(request.form, text, stars, prediction)
        
        mycursor = myDb.cursor()
        
        sql = "INSERT INTO reviews (review, stars, sentiment) VALUES (%s, %s, %s)"
        value = (text, stars, bool(prediction[0]))

        mycursor.execute(sql, value)

        myDb.commit()
        
        mycursor.close()
        
        myresult= fetchAndUpdateAnalytics()
    
        if prediction:
            return render_template('index.html', prediction_text='The review is Positive', myresult=myresult)
        else:
            return render_template('index.html', prediction_text='The review is Negative.', myresult=myresult)


if __name__ == "__main__":
    app.run(debug=True)
