import os
import sys
import json
import requests
import connectorconfig
import urllib
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
        return acePublicSettingsJSON[settingName]

    def aceLogin(self, username, password):
        aceLoginRequestStr = self.aceBaseUrl + "?fct=login&accountId=" + self.aceAccountId + "&username=" + username + "&password=" + password + "&browserinfo=NULL&language=en-US&format=JSON"
        aceLoginGet = requests.get(aceLoginRequestStr)
        aceLoginJSON = json.loads(aceLoginGet.text)['results'][0]
        aceGuid = aceLoginJSON['GUID']
        return aceGuid

    def aceCreateTaskFromResult(self, result):
        summary = "DEFECT: %s" % result['custom_summary'][:100]
        summary = urllib.quote(summary)
        details = "Reported By: %s \n\n" % self.testrailGetUserName(result['created_by'])
        details += "Comments: %s \n\n" % result['comment']
        details += self.parseStepResults(result['custom_step_results'])
        details = urllib.quote(details)
        projectId = '21900'
        statusId = '81428'
        isDetailsPlainText = 'False'
        responseFormat = 'JSON'
        getTaskInReturn = 'True'
        guid = self.aceLogin(self.aceUsername, self.acePassword)
        createTaskStr = self.aceBaseUrl + "?fct=createtask&guid=" + guid + "&projectid=" + self.aceProjectId + "&summary=" + summary + "&statusid=" + statusId + "&isdetailsplaintext=" + isDetailsPlainText + "&gettaskinreturn=" + getTaskInReturn + "&format=" + responseFormat
        response = requests.get(createTaskStr)
        createTaskJSON = json.loads(response.text)['results'][0]
        createTaskId = createTaskJSON['TASK_ID']
        #details too long to fit in create request, using separate request to send test steps
        saveTaskStr = self.aceBaseUrl + "?fct=savetask&guid=" + guid + "&taskid=" + createTaskId + "&details=" + details
        saveTaskResponse = response.get(saveTaskStr)
        return createTaskId

    def parseStepResults(self, stepResults):
        parsedResult = ""
        resultText = ["", "Passed", "Blocked", "Untested", "Retest", "Failed", "Skipped"]
        if stepResults is not None:
            for result in stepResults:
                result_status = result['status_id']
                parsedResult += "Step Status: %s" % resultText[result_status] + "\n"
                parsedResult += "Step: %s" % result['content'] + "\n\n"
        return parsedResult

    def testrailGetResults(self, test_id):
        results = self.testrailClient.send_get('get_results/%s' % test_id)
        return results[0]

    def testrailGetUserName(self, user_id):
        user = self.testrailClient.send_get('get_user/%s' % user_id)
        name = user['name']
        return name

@app.route("/")
def main():
    test_id = request.args.get('test_id', '')
    connector = TestrailAceConnector()
    testResult = connector.testrailGetResults(test_id)
    stepResults = testResult['custom_step_results']
    aceTaskId = connector.aceCreateTaskFromResult(testResult)
    return redirect('http://mercurygate.aceproject.com/?TASK_ID=%s' % aceTaskId)

if __name__ =='__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
