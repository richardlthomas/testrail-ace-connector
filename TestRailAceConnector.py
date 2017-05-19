import os
import sys
import json
import requests
import connectorconfig
sys.path.append('/Users/richard.thomas/testrail-api/python/2.x')
from flask import Flask
from testrail import *

app = Flask(__name__)

class TestrailAceConnector:
    testrailClient = APIClient("https://mercurygateqa.testrail.net/")
    testrailClient.user = connectorconfig.testRailUsername
    testrailClient.password = connectorconfig.testRailPassword
    aceBaseUrl = "http://api.aceproject.com/"
    aceAccountID = "mercurygate"
    test = testrailClient.send_get('get_test/47')
    testJson = json.loads(json.dumps(test, indent=3))
    print testJson['title']

    def acePublicSettings(self, settingName="CUSTOM_PRODUCT_NAME"):
        acePublicSettingsGet = requests.get(self.aceBaseUrl + "?fct=getpublicsettings&accountId=" + self.aceAccountID + "&format=JSON")
        acePublicSettingsJSON = json.loads(acePublicSettingsGet.text)['results'][0]
        print acePublicSettingsJSON[settingName]
        return acePublicSettingsJSON[settingName]

    def aceLogin(self, username, password):
        aceLoginRequestStr = self.aceBaseUrl + "?fct=login&accountId=" + self.aceAccountID + "&username=" + username + "&password=" + password + "&browserinfo=NULL&language=en-US&format=JSON"
        aceLoginGet = requests.get(aceLoginRequestStr)
        aceLoginJSON = json.loads(aceLoginGet.text)['results'][0]
        aceGuid = aceLoginJSON['GUID']
        print aceGuid
        return aceGuid

    def getFailedTests(self):
        failures = self.testrailClient.send_get('get_tests/9&status_id=5')
        print failures
        return failures

    def getOpenTestRuns(self):
        allRuns = self.testrailClient.send_get('get_runs/5')
        openRuns = []
        print("Open test runs:")
        for run in allRuns:
            run = json.loads(json.dumps(run))
            if run['is_completed'] == False:
                openRuns.append(run)
        print openRuns
        return openRuns

@app.route("/")
def main():
    connector = TestrailAceConnector()
    aceUsername = connectorconfig.aceUsername
    acePassword = connectorconfig.acePassword
    connector.acePublicSettings()
    connector.aceLogin(aceUsername, acePassword)
    connector.getFailedTests()
    connector.getOpenTestRuns()
    return "Works"

if __name__ =='__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
