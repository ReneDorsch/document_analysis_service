import time

from app.core.apis import ContextAnalyzer, util_functions
from app.core.Datamodels.IO_Models import InputData
from fastapi import FastAPI
import uvicorn
import queue
import threading
from app.core.Datamodels.Task import Task
from fastapi.encoders import jsonable_encoder
from app.core import config
from app.core.apis.util_functions import save_data, save_as_json

app = FastAPI()
queue = queue.Queue()




def context_worker():
    '''
    Defines the Worker Thread to execute the extraction task from the PDF-Documnet
    :return: The extracted Document to the Requester
    '''
    while True:
        task = queue.get()
        if task.is_break():

            break

        print("ok")


        # Creates a new Object to Analyze the data
        context_analyzer = ContextAnalyzer()
        context_analyzer.parse_data_from_api(task.get_data())

        # Start Processing
        context_analyzer.preprocess()
        context_analyzer.process()

        # Send the extracted information to the requester
        data = context_analyzer.save_data()

        # Make Backup of Data
        save_as_json(data, task.get_path())

        # Delete the Task to keep everything small and easy
        del task
        context_analyzer.postprocess()
        print("Task done")
        queue.task_done()

@app.post('/api/contextualize_data')
def contextualize_data(document: InputData):

    # The Path to the requester
    # For now direct, but should be over the header of the request data
    requester = "http://0.0.0.0:8005/get_annotated_doc"

    file = jsonable_encoder(document)
    req_doc_id = document.document_id

    # Log data:
    # utilities.log_date(file)
    # Read the file uploaded by the user
    path_to_data = save_data(file)

    task = Task(path_to_data, '', document, 'annotate_document', requester, req_doc_id)
    # Load data in queue to extract the data
    queue.put(task)
    time.sleep(1)
    return {'Result': '200'}

if __name__ == '__main__':

    if config.debug_mode:
         #####################################################################
        # ### Context Analysis
        import torch
        print(torch.cuda.is_available())
        cont = ContextAnalyzer()
        cont.readJson("logging/Input/test_04_21_2021_14_06_41.json.json")
        cont.preProcess()
        cont.processData()

    else:
        print("ok")
        thread = threading.Thread(target=context_worker)
        thread.start()
        uvicorn.run(app, port=8007, host='0.0.0.0')
