def get_kube_client(project, zone, cluster):
    import google.auth
    import kubernetes

    BASE_URL = 'https://container.googleapis.com/v1beta1/'

    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    if not credentials.valid:
        credentials.refresh(google.auth.transport.requests.Request())

    authed_session = google.auth.transport.requests.AuthorizedSession(credentials)
    res = authed_session.get(f'{BASE_URL}projects/{project}/locations/{zone}/clusters/{cluster}')

    res.raise_for_status()

    cluster_info = res.json()

    config = kubernetes.client.Configuration()

    config.host = f"https://{cluster_info['endpoint']}"
    config.verify_ssl = False
    config.api_key = {"authorization": f'Bearer {credentials.token}'}
    client = kubernetes.client.ApiClient(config)

    return kubernetes.client.AppsV1Api(client)

# reference: https://www.toptal.com/devops/better-google-cloud-continuous-deployment
def deploy_to_k8s(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
                        event. The `@type` field maps to
                         `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
                        The `data` field maps to the PubsubMessage data
                        in a base64-encoded string. The `attributes` field maps
                        to the PubsubMessage attributes if any is present.
         context (google.cloud.functions.Context): Metadata of triggering event
                        including `event_id` which maps to the PubsubMessage
                        messageId, `timestamp` which maps to the PubsubMessage
                        publishTime, `event_type` which maps to
                        `google.pubsub.topic.publish`, and `resource` which is
                        a dictionary that describes the service API endpoint
                        pubsub.googleapis.com, the triggering topic's name, and
                        the triggering event type
                        `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    Returns:
        None. The output is written to Cloud Logging.
    """
    import base64
    import json
    import logging

    print("""This Function was triggered by messageId {} published at {} to {}
    """.format(context.event_id, context.timestamp, context.resource["name"]))


    if 'data' in event:
        name = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
        if "action" in data and "tag" in data:
            if data["action"] == "INSERT" and "-staging:latest" in data["tag"]:

                project = 'robust-heaven-344812'
                zone = 'us-central1-c'
                cluster = 'cluster-1'

                # TODO: Since I can't connect to the new private cluster I can't create 
                #       a deployment from kubectl, create one and edit this. Also the 
                #       manifest I was using was valid for my test images, not the new 
                #       microservices
                deployment = 'project-staging'
                # target_container = os.environ.get('CONTAINER')

                v1 = get_kube_client(project, zone, cluster)

                # TODO: Failing for the private cluster, worked fine for public
                dep = v1.read_namespaced_deployment(deployment, 'staging-test')
                if dep is None:
                    logging.error(f'There was no deployment named {deployment}')
                    return

                # for i, container in enumerate(dep.spec.template.spec.containers):
                #     if container.name == target_container:
                #         dep.spec.template.spec.containers[i].image = image
                # logging.info(f'Updating to {image}')

                # TODO: figure out how to re-apply deployment, last I remember
                #       that I was trying to get the deployment to re-pull the image
                #       I guess I should follow the reference and patch the
                #       target_container
                v1.replace_namespaced_deployment(deployment, 'staging-test', dep)

        print('DIFFERENT {}!'.format(name))
