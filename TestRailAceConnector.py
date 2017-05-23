import os
import sys
import json
import requests
import connectorconfig
sys.path.append('/Users/richard.thomas/testrail-api/python/2.x')
from flask import Flask, request, jsonify, redirect
from testrail import *

app = Flask(__name__)

class TestrailAceConnector:
    testrailClient = APIClient("https://mercurygateqa.testrail.net/")
    testrailClient.user = connectorconfig.testRailUsername
    testrailClient.password = connectorconfig.testRailPassword
    aceBaseUrl = "http://api.aceproject.com/"
    aceAccountId = "mercurygate"
    aceProjectId = '21900'
    aceUsername = connectorconfig.aceUsername
    acePassword = connectorconfig.acePassword

    def acePublicSettings(self, settingName="CUSTOM_PRODUCT_NAME"):
        acePublicSettingsGet = requests.get(self.aceBaseUrl + "?fct=getpublicsettings&accountId=" + self.aceAccountId + "&format=JSON")
        acePublicSettingsJSON = json.loads(acePublicSettingsGet.text)['results'][0]
        #print acePublicSettingsJSON[settingName]
        return acePublicSettingsJSON[settingName]

    def aceLogin(self, username, password):
        aceLoginRequestStr = self.aceBaseUrl + "?fct=login&accountId=" + self.aceAccountId + "&username=" + username + "&password=" + password + "&browserinfo=NULL&language=en-US&format=JSON"
        aceLoginGet = requests.get(aceLoginRequestStr)
        aceLoginJSON = json.loads(aceLoginGet.text)['results'][0]
        aceGuid = aceLoginJSON['GUID']
        #print aceGuid
        return aceGuid

    def aceCreateTaskFromResult(self, result):
        summary = "DEFECT: %s" % result['custom_summary'][:100]
        details = "Reported By: %s \n\n" % self.testrailGetUserName(result['created_by'])
        details += "Comments: %s \n\n" % result['comment']
        details += self.parseStepResults(result['custom_step_results'])
        projectId = '21900'
        statusId = '81428'
        isDetailsPlainText = 'True'
        responseFormat = 'JSON'
        getTaskInReturn = 'True'
        guid = self.aceLogin(self.aceUsername, self.acePassword)
        createTaskStr = self.aceBaseUrl + "?fct=createtask&guid=" + guid + "&projectid=" + self.aceProjectId + "&summary=" + summary + "&details=" + details + "&statusid=" + statusId + "&isdetailsplaintext=" + isDetailsPlainText + "&gettaskinreturn=" + getTaskInReturn + "&format=" + responseFormat
        response = requests.get(createTaskStr)
        createTaskJSON = json.loads(response.text)['results'][0]
        createTaskId = createTaskJSON['TASK_ID']
        return createTaskId

    def parseStepResults(self, stepResults):
        parsedResult = ""
        for result in stepResults:
            if result['status_id'] == 5:
                parsedResult += "Failed: %s" % result['content'] + "\n\n"
                parsedResult += "Expected: %s" % result['expected'] + "\n\n"
                parsedResult += "Actual: %s" % result['actual'] + "\n\n"
        return parsedResult

    def getFailedTests(self):
        failures = self.testrailClient.send_get('get_tests/9&status_id=5')
        #print failures
        return failures

    def getOpenTestRuns(self):
        allRuns = self.testrailClient.send_get('get_runs/5')
        openRuns = []
        #print("Open test runs:")
        for run in allRuns:
            run = json.loads(json.dumps(run))
            if run['is_completed'] == False:
                openRuns.append(run)
        #print openRuns
        return openRuns

    def testrailGetResults(self, test_id):
        results = self.testrailClient.send_get('get_results/%s' % test_id)
        return results[0]

    def testrailGetUserName(self, user_id):
        user = self.testrailClient.send_get('get_user/%s' % user_id)
        name = user['name']
        return name

@app.route("/")
def main():
    #return request.args.get('test_id', '')
    test_id = request.args.get('test_id', '')
    connector = TestrailAceConnector()
    testResult = connector.testrailGetResults(test_id)
    stepResults = testResult['custom_step_results']
    aceTaskId = connector.aceCreateTaskFromResult(testResult)
    return redirect('http://mercurygate.aceproject.com/?TASK_ID=%s' % aceTaskId)

if __name__ =='__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
