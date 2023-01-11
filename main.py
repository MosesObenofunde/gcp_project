from google.cloud import asset_v1
from pprint import pprint
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google import pubsub_v1
from google.cloud import functions_v2
from google.oauth2 import service_account
import google.auth
import google.auth.transport.requests
import requests
from google.cloud import compute_v1
import json
import pprint
import os

credentials = GoogleCredentials.get_application_default()

cred, prj = google.auth.default( scopes='https://www.googleapis.com/auth/cloud-platform')   
auth_req = google.auth.transport.requests.Request()
cred.refresh(auth_req)
id_token=cred.token
headers= {"Authorization": f"Bearer {id_token}"} 


project_id=os.environ.get('GCP_PROJECT')
query="NOT labels.autodelete=false"

def get_resources(project_id,asset_types,query,read_mask):
  project_resource = "projects/{}".format(project_id)
  client = asset_v1.AssetServiceClient()
  
  response = client.search_all_resources(
      request={
          "scope": project_resource,
          "query": query,
          "asset_types": asset_types,
          "read_mask": read_mask,
      }
  )
  return response



# Delete Disk
def delete_disk():
  asset_types=["compute.googleapis.com/Disk"]
  read_mask="name,location,displayName,labels"
  service = discovery.build('compute', 'v1', credentials=credentials)
  result=get_resources(project_id,asset_types,query,read_mask)       
  for item in  result:
    print("Deleting "+item.name)
    request = service.disks().delete(project=project_id, zone=item.location, disk=item.display_name)
    request.execute()

# Delete Firewall
def delete_firewall():
  asset_types=["compute.googleapis.com/Firewall"]
  read_mask="name,location,displayName,description"
  query=""
  result=get_resources(project_id,asset_types,query,read_mask)    
  for item in  result:
    if "autodelete=false" not in item.description:        
      print("Deleting "+item.name)
      service = discovery.build('compute', 'v1', credentials=credentials)
      request = service.firewalls().delete(project=project_id, firewall=item.display_name)  
      request.execute()

# Delete Address
def delete_address():
  asset_types=["compute.googleapis.com/Address"]
  read_mask="name,location,displayName,labels,state"

  service = discovery.build('compute', 'v1', credentials=credentials)
  result=get_resources(project_id,asset_types,query,read_mask)
  for item in result:
    if item.state == "RESERVED":
      print("Deleting "+item.name)
      request = service.addresses().delete(project=project_id, region=item.location, address=item.display_name)
      request.execute()
    
# Delete PubSub
def delete_pubsub():
  asset_types=["pubsub.googleapis.com/Topic", "pubsub.googleapis.com/Subscription"]
  read_mask="name,location,displayName,labels,assetType"

  result=get_resources(project_id,asset_types,query,read_mask)    
  for item in result:
    if "Topic" in item.asset_type:    
      print("Deleting "+item.name)
      client = pubsub_v1.PublisherClient()
      request = pubsub_v1.DeleteTopicRequest(
        topic=item.display_name,
      )    
      client.delete_topic(request=request)
    if "Subscription" in item.asset_type:
      print("Deleting "+item.name)
      client = pubsub_v1.SubscriberClient()
      request = pubsub_v1.DeleteSubscriptionRequest(
        subscription=item.display_name,
      ) 
      client.delete_subscription(request=request)

# Delete Cloud Function
def delete_function():
  asset_types=["cloudfunctions.googleapis.com/CloudFunction"]
  read_mask="name,location,displayName,labels"
  result=get_resources(project_id,asset_types,query,read_mask)
  
  for item in result:
    print("Deleting "+item.name)
    fun=item.name.split("cloudfunctions.googleapis.com/")[1]
    url="https://cloudfunctions.googleapis.com/v1/"+fun    
    res = requests.delete(url, headers=headers) 
    print(res.content)

def delete_cloudrun():
  asset_types=["run.googleapis.com/Service"]
  read_mask="name,location,displayName,labels"
  result=get_resources(project_id,asset_types,query,read_mask)
  
  for item in result:
    print("Deleting "+item.name)
    svc=item.name.split("run.googleapis.com/")[1]
    url="https://run.googleapis.com/v1/"+svc  
    res = requests.delete(url, headers=headers) 
    print(res.content)


def delete_instance():
  asset_types=["compute.googleapis.com/Instance"]
  read_mask="name,location,displayName,labels"
  result=get_resources(project_id,asset_types,query,read_mask)

  for item in result:
    print("Deleting "+item.name)
    instance_client = compute_v1.InstancesClient()
    try:
      operation = instance_client.delete(
          project=project_id, zone=item.location, instance=item.display_name
      )
    except:
      print("Failed to delete the instance, please check the delete protection configurations")
      
def delete_gke_cluster():
  service = discovery.build('container', 'v1',credentials=credentials)
  parent = "projects/"+project_id+"/locations/-"   
  req=service.projects().locations().clusters().list(parent=parent)
  res = req.execute()
  try:
    for cluster in res['clusters']:
      try:
       if cluster["resourceLabels"]["autodelete"] != "false":
          n=cluster["selfLink"].split("container.googleapis.com/v1/")[1]
          name=n.replace("zones", "locations" )
          print("Deleting "+name)
          request = service.projects().locations().clusters().delete(name=name)
          request.execute() 
      except:
        n=cluster["selfLink"].split("container.googleapis.com/v1/")[1]
        name=n.replace("zones", "locations" )
        print("Deleting "+name)
        request = service.projects().locations().clusters().delete(name=name)
        request.execute()
  except:
    pass

def delete_sql():
  asset_types=["sqladmin.googleapis.com/Instance"]
  read_mask="name,location,displayName,labels"
  result=get_resources(project_id,asset_types,query,read_mask)

  for item in result:
    print("Deleting "+item.name)
    instance=item.name.split("cloudsql.googleapis.com/")[1]
    url="https://sqladmin.googleapis.com/v1/"+instance
    res = requests.delete(url, headers=headers) 
    print(res.content)
    
def delete_bucket():
  asset_types=["storage.googleapis.com/Bucket"]
  read_mask="name,location,displayName,labels"
  result=get_resources(project_id,asset_types,query,read_mask)

  for item in result:
    print("Deleting "+item.name)
    url="https://storage.googleapis.com/storage/v1/b/"+item.display_name
    res = requests.delete(url, headers=headers) 
    print(res.content)
    
def delete_app_engine_service():
  asset_types=["appengine.googleapis.com/Service"]
  read_mask="name,location,displayName,labels"   
  result=get_resources(project_id,asset_types,query,read_mask)

  for item in result:
    print("Deleting "+item.name)
    url="https://appengine.googleapis.com/v1/apps/"+project_id+"/services/"+item.display_name
    res = requests.delete(url, headers=headers) 
    print(res.content)
    
    
def gcp_nuke(request):
  request_json = request.get_json()
  delete_app_engine_service() 
  delete_cloudrun() 
  delete_bucket() 
  delete_sql()   
  delete_gke_cluster()    
  #delete_function()    
  delete_pubsub()  
  delete_instance() 
  delete_address() 
  delete_firewall() 
  delete_disk()
  return "success"
