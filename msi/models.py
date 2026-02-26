# Radon Copyright 2023, University of Oxford
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.db import models

from radon.model.config import cfg
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.notification import (
    create_collection_fail,
    create_resource_fail,
    create_resource_request,
    create_resource_success,
    create_group_fail,
    create_user_fail,
    delete_collection_fail,
    delete_resource_fail,
    delete_group_fail,
    delete_user_fail,
    update_collection_fail,
    update_resource_fail,
    update_group_fail,
    update_user_fail,
    wait_response,
)
from radon.model.payload import (
    PayloadCreateCollectionRequest,
    PayloadCreateCollectionFail,
    PayloadCreateResourceRequest,
    PayloadCreateResourceFail,
    PayloadCreateResourceSuccess,
    PayloadCreateGroupRequest,
    PayloadCreateGroupFail,
    PayloadCreateUserRequest,
    PayloadCreateUserFail,
    PayloadDeleteCollectionRequest,
    PayloadDeleteCollectionFail,
    PayloadDeleteResourceRequest,
    PayloadDeleteResourceFail,
    PayloadDeleteGroupRequest,
    PayloadDeleteGroupFail,
    PayloadDeleteUserRequest,
    PayloadDeleteUserFail,
    PayloadUpdateCollectionRequest,
    PayloadUpdateCollectionFail,
    PayloadUpdateResourceRequest,
    PayloadUpdateResourceFail,
    PayloadUpdateGroupRequest,
    PayloadUpdateGroupFail,
    PayloadUpdateUserRequest,
    PayloadUpdateUserFail,
)
from radon.model.microservices import Microservices
from radon.util import (
    merge,
    payload_check,
    split
)
from radon.model import payload



P_META_SENDER = "/meta/sender"
P_OBJ_CONTAINER = "/obj/container"
P_OBJ_NAME = "/obj/name"
P_OBJ_LOGIN = "/obj/login"

MSG_INFO_MISSING = "Information is missing for the {}: {}"
MSG_MISSING_OBJ = "Missing object in payload"


def msi_test(params):
    msg = params.get('msg', '')
    return {"out" : msg * 2}


def msi_create_collection(payload_json):
    ok, _, msg = Microservices.create_collection(PayloadCreateCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_group(payload_json):
    ok, _, msg = Microservices.create_group(PayloadCreateGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_resource(payload_json):
    ok, _, msg = Microservices.create_resource(PayloadCreateResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_user(payload_json):
    ok, _, msg = Microservices.create_user(PayloadCreateUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_collection(payload_json):
    ok, _, msg = Microservices.delete_collection(PayloadDeleteCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_group(payload_json):
    ok, _, msg = Microservices.delete_group(PayloadDeleteGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_resource(payload_json):
    ok, _, msg = Microservices.delete_resource(PayloadDeleteResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_user(payload_json):
    ok, _, msg = Microservices.delete_user(PayloadDeleteUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_collection(payload_json):
    ok, _, msg = Microservices.update_collection(PayloadUpdateCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_group(payload_json):
    ok, _, msg = Microservices.update_group(PayloadUpdateGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_resource(payload_json):
    ok, _, msg = Microservices.update_resource(PayloadUpdateResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_user(payload_json):
    ok, _, msg = Microservices.update_user(PayloadUpdateUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def adios_workflow(payload_json):
    import tempfile
    import pickle
    import os
    import shutil
    from adios2 import Stream
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    import lime
    import lime.lime_tabular
    import matplotlib.pyplot as plt
    import mlflow
    from mlflow.models import infer_signature
    
    temp_dir = tempfile.mkdtemp()
    print(temp_dir)
    
    radon_path = payload_json['path']
    resc = Resource.find(radon_path)
    basename = resc.get_name().replace(".csv", "")
    metadata = resc.get_cdmi_user_meta()
    
    csv_path = temp_dir + os.sep + resc.get_name()
    fp_csv = open(csv_path, "wb")
    for chunk in resc.chunk_content():
        fp_csv.write(chunk)
    fp_csv.close()
    
    # Loading the CSV data to pandas dataframe

    df1 = pd.read_csv(csv_path) ### Path to the data file
    df1['class'] = df1['class'].replace({'P': 0, 'H': 1})
    
    # -----------------------------------------------------------------
    #       Writing Python Dataframe to Adios Format Conversion        |
    # -----------------------------------------------------------------
    
    def write_df_to_adios(df, adios_filename):
        
        with Stream(adios_filename, "w") as fh:  # Open file in write mode
                for col in df.columns:  # Iterate over each column of the DataFrame
                    if col == 'ID':
                        continue
                    col_data = df[col].values 
                    
                    # Handle numeric data types (int or float)
                    if pd.api.types.is_numeric_dtype(col_data):
                        
                        fh.write(col, col_data, [len(col_data)], [0], [len(col_data)])
                    else:
                        print(f"Skipping unsupported data type in column {col}")
        
                
                print(f"DataFrame with {df.shape[1]} columns written to {adios_filename} successfully.")
    
    # Specifying the output file path for the ADIOS2 format to store the converted data
    adios_filename = temp_dir + os.sep + basename + ".bp"
    # Write the DataFrame to ADIOS2 format
    write_df_to_adios(df1, adios_filename)
    
    
    shutil.make_archive(temp_dir + os.sep + basename + ".bp", 
                        "zip", 
                        temp_dir + os.sep + basename + ".bp")
    f = open(temp_dir + os.sep + basename + ".bp.zip", "rb")
    adios_bp_zip = f.read()
    f.close()
    
    params = {
        "name" : basename + ".bp",
        "container": resc.get_container(),
        "mimetype": "application/adios",
        "size": len(adios_bp_zip),
        "metadata": { 
            "provenance data": resc.get_path()
         }
    }
    adios_zip_resc = Resource.create(**params)
    if adios_zip_resc:
        adios_zip_resc.put(adios_bp_zip)
        
        payload_json = {
            "obj": adios_zip_resc.mqtt_get_state(),
            'meta' : {"sender": "rule_engine"}
        }
        create_resource_success(PayloadCreateResourceSuccess(payload_json))
    
    
    # ---------------------------------------------------------------
    #       Reading data from Adios Format to Python Dataframe       |
    # ---------------------------------------------------------------

    def read_adios_to_df(adios_filename):
        # Open ADIOS2 file in read mode
        with Stream(adios_filename, "r") as fh:
            data_dict = {}
            
            # Read data from the file step by step
            for fstep in fh:
                # Iterate over all available variables in the current step
                for variable_name, variable_info in fstep.available_variables().items():
                    
                    data = fstep.read(variable_name)
                    data_dict[variable_name] = data
                  
                break

        # Create a pandas DataFrame from the dictionary of variables
        # Ensure all values in the dictionary are lists (if necessary)
        for key in data_dict.keys():
            if not isinstance(data_dict[key], list):
                data_dict[key] = [data_dict[key]]  # Convert scalar to a single-element list

        df = pd.DataFrame(data_dict)
        return df


    # Path of adios file to be read
    adios_filename = temp_dir + os.sep + "data.bp"
    df_read = read_adios_to_df(adios_filename)

    # -----------------------------------------------
    #       Data Pre-Processing and Preparation      |
    # -----------------------------------------------


    # Assuming df_read is your 1x471 DataFrame
    # Each entry in df_read contains an array of 174 values.
    # We will use apply(pd.Series) to expand each column
    expanded_df = pd.DataFrame()

    for col in df_read.columns:
        expanded_col = pd.DataFrame(df_read[col].values[0])  # Extract the array and convert to DataFrame
        expanded_col.columns = [col]  # Assign the column name
        expanded_df = pd.concat([expanded_df, expanded_col], axis=1)  # Concatenate columns



    # Step 1: Separate features (X) and target (y)
    X = expanded_df.drop('class', axis=1)  # All columns except the target
    y = expanded_df['class']  # The target column

    # Step 2: Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Step 3: Scaling the data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)


    # -----------------------------------------------
    #       Model Training and Testing               |
    # -----------------------------------------------

    ### Model Training
    ## MLflow server setup
    mlflow.set_tracking_uri(uri='http://127.0.0.1:5000')
    ml_params = {
        'n_estimators': 100,      # Number of trees
        'max_depth': 25,          # Max depth of the tree
        'random_state': 42,       # Random state for reproducibility
    }

    # Selected Model is RandomForest 
    model = RandomForestClassifier(**ml_params)
    model.fit(X_train_scaled, y_train)
    
    
    

    ### Model Testing

    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print(f'Accuracy of the model is : {accuracy:.4f}')
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1 Score: {f1}")
    
    
    host_url = mlflow.get_registry_uri()
    experiment_url = host_url

    mlflow.set_experiment("Machine Learning Model For Adios Usecase")
    with mlflow.start_run():
        # Log the hyperparameters
        mlflow.log_params(ml_params)
    
        # Log the loss metric
        mlflow.log_metric("Accuracy", accuracy)
        mlflow.log_metric("Precision", precision)
        mlflow.log_metric("Recall", recall)
        mlflow.log_metric("F1_Score", f1)
        
        
    
        # Set a tag that we can use to remind ourselves what this run was for
        mlflow.set_tag("Training Info", "Random Forest model for classification of Alzheimer diesease patients using the handwritting data.")
    
        # Infer the model signature
        signature = infer_signature(X_train_scaled, model.predict(X_train_scaled))
    
        # Log the model
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="Adios_ML_Workflow",
            signature=signature,
            input_example=X_train_scaled,
            registered_model_name="Randomforest_classifier",
        )
        
        
        run = mlflow.active_run()
        experiment_id = run._info.experiment_id
        experiment_url = f"{host_url}/#/experiments/{experiment_id}"
    
    dump_model = pickle.dumps(model)
    
    if "model_path" in metadata:
        container, name = split(metadata["model_path"])
    else:
        container = resc.container
        name = resc.get_name().replace("csv", "model")
    
    params = {
        "name" : name,
        "container": container,
        "mimetype": "application/octet-stream",
        "size": len(dump_model),
        "metadata": { "provenance data": resc.get_path(),
                      "param_n_estimator" : ml_params['n_estimators'],
                      "param_random_state" : ml_params['random_state'],
                      "param_max_depth" : ml_params['max_depth'],
                      "experiment_url" : experiment_url
                    }
    }
    model_resc = Resource.create(**params)
    if model_resc:
        model_resc.put(dump_model)
        
        payload_json = {
            "obj": model_resc.mqtt_get_state(),
            'meta' : {"sender": "rule_engine"}
        }
        create_resource_success(PayloadCreateResourceSuccess(payload_json))
    
    # ---------------------------------------------------------
    #     Function to convert the Inference sample to Adios    |
    # ---------------------------------------------------------

    def write_sample_to_adios(sample, adios_filename):
        # Ensure sample is a contiguous NumPy array
        sample_array = np.asarray(sample[0]).flatten().copy()  # Flatten the array if necessary
        shape = sample_array.shape  # Get shape for defining variable

        # Initialize ADIOS2 IO and set the filename
        with Stream(adios_filename, "w") as fh:  # Open file in write mode    
            fh.write('Test_Sample', sample_array, shape, [0], [shape[0]])  # Writing the sample

        print(f"Sample data written to {adios_filename} successfully.")

    # Specify the output ADIOS2 file path
    adios_filename = temp_dir + os.sep + 'sample_data.bp'
    
    shutil.make_archive(temp_dir + os.sep + "sample_" + basename + ".bp", 
                        "zip", 
                        temp_dir + os.sep + "sample_" + basename + ".bp")
    f = open(temp_dir + os.sep + "sample_" + basename + ".bp.zip", "rb")
    adios_sample_bp_zip = f.read()
    f.close()
    
    params = {
        "name" : "sample_" + basename + ".bp",
        "container": resc.get_container(),
        "mimetype": "application/adios",
        "size": len(adios_sample_bp_zip),
        "metadata": { 
            "provenance data": resc.get_path(),
            "provenance model": model_resc.get_path(),
         }
    }
    
        
    adios_sample_zip_resc = Resource.create(**params)
    if adios_sample_zip_resc:
        adios_sample_zip_resc.put(adios_sample_bp_zip)
        
        payload_json = {
            "obj": adios_sample_zip_resc.mqtt_get_state(),
            'meta' : {"sender": "rule_engine"}
        }
        create_resource_success(PayloadCreateResourceSuccess(payload_json))



    # ---------------------------------------------------------
    #     Function to Read the Inference sample from Adios    |
    # ---------------------------------------------------------


    def read_sample_from_adios2(adios_filename):
        sample = None
        
        with Stream(adios_filename, "r") as fh:
            # Read data from the file step by step
            for fstep in fh:
                # Iterate over all available variables in the current step
                for variable_name, variable_info in fstep.available_variables().items():
                    # Read the data for this variable
                    data = fstep.read(variable_name)

                    if variable_name == 'Test_Sample':
                        sample = np.array(data)  # Convert to numpy array
                    else :
                        print('Feature not found')

                # Since we want to read only the first step for simplicity
                break

        # Check if the variables were read successfully
        if sample is None:
            raise ValueError("Sample not found in the ADIOS2 file.")

        return sample

    # -----------------------------------------------
    #       Model Explaination using LIME           |
    # -----------------------------------------------


    explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=X_train_scaled,
        feature_names=X.columns,
        class_names=['Class 0', 'Class 1'],  # Adjust for your class labels
        mode='classification'
    )

    ## Selecting Sample for Inferene 
    choosen_instance = X_test_scaled[2].reshape(1, -1)

    # converting the sample to Adios 
    write_sample_to_adios(choosen_instance, adios_filename)
    # Reading Inference test data from Adios
    sample_data  = read_sample_from_adios2(temp_dir + os.sep + 'sample_data.bp')
    ## Generating the prediction and explaination of the inference

    exp = explainer.explain_instance(
        data_row=sample_data,  # instance to explain
        predict_fn=model.predict_proba  # prediction function of the model
    )


    # -----------------------------------------------
    #       LIME explaination to Adios              |
    # -----------------------------------------------



    def write_lime_explanation_to_adios2(exp, adios_filename):
        """
        Write the LIME explanation (exp) to an ADIOS2 file format using Stream.

        Parameters:
        exp: LIME explanation object from lime.explain_instance.
        adios_filename: str, name of the output file in ADIOS2 format.
        """
        contributions = exp.as_list()
        feature_names = [item[0] for item in contributions]
        contribution =[item[1] for item in contributions]
        prediction_scores = exp.predict_proba
        prediction_scores_arr = np.array(prediction_scores, dtype=np.float32)

        with Stream(adios_filename, "w") as fh:  
            fh.write('contributions', contribution, [len(contributions)], [0], [len(contributions)])
            fh.write('prediction_scores', prediction_scores_arr, [len(prediction_scores_arr)], [0], [len(prediction_scores_arr)])
            fh.write_attribute('Feature_Name',feature_names)
            

        print(f"LIME explanation saved to {adios_filename} in ADIOS2 format.")


    # function take two parameter, first lime explaination and second the path to save the explaination in adios format
    write_lime_explanation_to_adios2(exp, temp_dir + os.sep + 'explanation_data.bp')

    # ------------------------------------------------------
    #      Reading LIME explaination from Adios to Lists    |
    # ------------------------------------------------------



    def read_lime_explanation_from_adios2(adios_filename):
        contributions = None
        predicted_scores = None
        Features=[]
        # Open ADIOS2 file in read mode
        with Stream(adios_filename, "r") as fh:
            for fstep in fh:
                for variable_name, variable_info in fstep.available_variables().items():
            
                    data = fstep.read(variable_name)
                    if variable_name == 'contributions':
                        contributions = np.array(data)  # Convert to numpy array
                    elif variable_name == 'prediction_scores':
                        predicted_scores = np.array(data)  # Convert to numpy array
                for attribute_name, variable_info in fstep.available_attributes().items():  
                    data = fstep.read_attribute(attribute_name)
                    if attribute_name =='Feature_Name':
                        Features = data

                break

        # Check if the variables were read successfully
        if contributions is None:
            raise ValueError("Contributions not found in the ADIOS2 file.")
        if predicted_scores is None:
            raise ValueError("Predicted scores not found in the ADIOS2 file.")

        return contributions, predicted_scores,Features

    # path where the LIME eplaination in Adios foramt is saved
    adios_filename = temp_dir + os.sep + 'explanation_data.bp'
    contributions, predicted_scores, Features = read_lime_explanation_from_adios2(adios_filename)

    predicted_probabilities = exp.predict_proba 
    predicted_class = 0 if predicted_probabilities[0] > predicted_probabilities[1] else 1
    print("Predicted Class:", predicted_class)
    
    shutil.make_archive(temp_dir + os.sep + "explanation_" + basename + ".bp", 
                        "zip", 
                        temp_dir + os.sep + "explanation_" + basename + ".bp")
    f = open(temp_dir + os.sep + "explanation_" + basename + ".bp.zip", "rb")
    adios_explanation_bp_zip = f.read()
    f.close()
    
    params = {
        "name" : "explanation_" + basename + ".bp",
        "container": resc.get_container(),
        "mimetype": "application/adios",
        "size": len(adios_explanation_bp_zip),
        "metadata": { 
            "provenance data": resc.get_path(),
            "provenance model": model_resc.get_path(),
            "predicted class": predicted_class,
         }
    }
    
    adios_explanation_zip_resc = Resource.create(**params)
    if adios_explanation_zip_resc:
        adios_explanation_zip_resc.put(adios_explanation_bp_zip)
        
        payload_json = {
            "obj": adios_explanation_zip_resc.mqtt_get_state(),
            'meta' : {"sender": "rule_engine"}
        }
        create_resource_success(PayloadCreateResourceSuccess(payload_json))
    
    
    # ------------------------------------------------------
    #      Visualising the LIME output                     |
    # ------------------------------------------------------

    plt.figure(figsize=(10, 6))
    plt.barh(Features,contributions, color=['blue' if x > 0 else 'red' for x in contributions])
    plt.xlabel('Contribution to Prediction')
    plt.title('LIME Feature Contributions')
    plt.axvline(0, color='black', linewidth=0.8, linestyle='--')  # Add a vertical line at 0 for reference
    plt.savefig(temp_dir + os.sep + "plot.png")
    #plt.show()
    f = open(temp_dir + os.sep + "plot.png", "rb")
    img_bytes = f.read()
    f.close()
    
    params = {
        "name" : resc.get_name().replace("csv", "png"),
        "container": resc.container,
        "mimetype": "image/png",
        "size": len(img_bytes),
        "metadata": { "provenance explanation data": adios_explanation_zip_resc.get_path(),
                      }
    }
    print(params)
    
    resc = Resource.create(**params)
    if resc:
        resc.put(img_bytes)
        
        payload_json = {
            "obj": resc.mqtt_get_state(),
            'meta' : {"sender": "rule_engine"}
        }
        create_resource_success(PayloadCreateResourceSuccess(payload_json))
    
    
    return {"ok": True, "msg" : "workflow executed"}


MICROSERVICES = {
    "test" : {
        "definition" : {
            "input" : [
                    {"name" : "msg", "type" : "str"}
                ],
            "output" : [
                    {"name" : "out", "type" : "str"}
                ],
        },
        "code" : msi_test
    },
    
    "create_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_collection
    },
    
    "create_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_resource
    },
    
    "create_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                    {"name" : "email", "type" : "str", "required" : False},
                    {"name" : "password", "type" : "str"},
                    {"name" : "administrator", "type" : "bool"},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_user
    },
    
    "create_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "err", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_group
    },
    
    "delete_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_collection
    },
    
    "delete_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_group
    },
    
    "delete_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_resource
    },
    
    "delete_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_user
    },
    
    "update_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_collection
    },
    
    "update_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_resource
    },
    
    "update_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                    {"name" : "email", "type" : "str", "required" : False},
                    {"name" : "fullname", "type" : "str", "required" : False},
                    {"name" : "password", "type" : "str"},
                    {"name" : "administrator", "type" : "bool"},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_user
    },
    "update_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                    {"name" : "members", "type" : "list", "required" : False},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_group
    },

    ##

    "adios_workflow" : {
        "definition" : {
            "input" : [
                    {"path" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : adios_workflow
    },

}

