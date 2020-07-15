import sqlite3
import requests
import numpy as np
import plotly.graph_objs as go
from sklearn.svm import SVR
import datetime


# create sqlite database to hold values from the API for easier retrieval
def create_db():
    conn = sqlite3.connect("locationData.db")
    c = conn.cursor()
    c.execute("drop table COVID_CASES_BY_DATE")
    c.execute(
        "create table COVID_CASES_BY_DATE (DATE_OF_RECORD INTEGER NOT NULL, STATE VARCHAR(2) NOT NULL, CASES INTEGER, DATE_STR VARCHAR(30)) ;")


# get data from api
def get_json():
    url_str = f'https://covidtracking.com/api/v1/states/daily.json'
    r = requests.get(url=url_str)
    data = r.json()

    return data


# populate database with the values we are interested in from the api
def populate_db():
    # create datafile object
    data = get_json()
    conn = sqlite3.connect("locationData.db")
    c = conn.cursor()

    # iterate thru objects returned from api and write their date in number and
    # string format, the state, and the total number of cases
    for item in data:
        if item["date"] is None:
            date = '000000000'
        if item["positive"] is None:
            cases = 0
        else:
            cases = item["positive"]
        state = item['state']
        date_str = str(item["lastUpdateEt"])
        date = int(item["date"])
        temp_str = f' INSERT OR REPLACE INTO COVID_CASES_BY_DATE(DATE_OF_RECORD, STATE, CASES,DATE_STR) VALUES({date},"{state}",{cases},"{date_str}")'
        # log sql string to console
        print(temp_str)
        c.execute(temp_str)
    conn.commit()

    c.execute("select * from COVID_CASES_BY_DATE")
    print(c.fetchall())


def get_distinct_states():
    conn = sqlite3.connect("locationData.db")
    c = conn.cursor()
    c.execute("select DISTINCT STATE from COVID_CASES_BY_DATE ORDER BY STATE")

    states_list = list(c.fetchall())

    return states_list


def get_list_from_db(str):
    conn = sqlite3.connect("locationData.db")
    c = conn.cursor()
    c.execute(str)
    states_list = list(c.fetchall())

    temp_list = []
    for item in states_list:
        temp_list.append(item[0])
    return temp_list


def show_model_predictions(x):
    print('show_model_Predictions runnning')
    states = get_distinct_states()

    # Test 3 different support vector machines to preform regressions using different models and use the one who's data fits best
    # Use the same error threshold on all models. This is to test which model is most accurate with the given data

    # svr_lin = SVR(kernel='linear', C=1e3)
    # svr_poly = SVR(kernel='poly', C=1e3, degree=2)  # degree of 2 because we have 2 params
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=.1)  # gamma is the amount of tolerance the model will have

    # Create figure to add line charts to
    fig = go.Figure()
    for state in states:
        # Get the cases, and dates for each state
        cases = get_list_from_db(
            f'SELECT CASES from COVID_CASES_BY_DATE WHERE STATE = "{state[0]}" ORDER BY DATE_OF_RECORD')
        dates = get_list_from_db(
            f'SELECT DATE_OF_RECORD from COVID_CASES_BY_DATE WHERE STATE = "{state[0]}" ORDER BY DATE_OF_RECORD')
        date_label = get_list_from_db(
            f'SELECT DATE_STR from COVID_CASES_BY_DATE WHERE STATE = "{state[0]}" ORDER BY DATE_OF_RECORD')

        # convert dates into a 1 column matrix for use with scikit.learn
        dates_fin = np.reshape(dates, (len(date_label), 1))

        # train rbf model for current state
        svr_rbf.fit(dates_fin, cases)

        # create a list of numbers and a list of days starting at 0 to predictions length(120)
        new_days = []
        nums = []
        last_date = datetime.datetime.today()
        for i in range(0, len(svr_rbf.predict(dates_fin))):
            new_days.append(str(last_date + datetime.timedelta(days=i))[5:10])
            nums.append(i)

        # add states data to figure as a scatter-line plot
        fig.add_scatter(x=nums, y=svr_rbf.predict(dates_fin), mode='lines', hovertext=state[0])
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=nums,
                ticktext=new_days
            )
        )

    # show figure containing all state data
    fig.show()
    pass


def main():
    # create_db()
    # populate_db()
    show_model_predictions(20)


if __name__ == "__main__":
    main()
