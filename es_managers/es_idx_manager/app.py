# Run Elasticsearch Curator from AWS Lambda.
#
# Edit serverless-curator.yaml to define which indices should be purged.
from __future__ import print_function

import certifi
import curator
import yaml
from curator.exceptions import NoIndices
from elasticsearch import Elasticsearch
import domovoi

app = domovoi.Domovoi()

@app.scheduled_function("rate(2 minutes)")
def handler(event, context):
    # For this function, we don't care about 'event' and 'context',
    # but they need to be in the function signature anyway.

    # with open('serverless-curator.yaml') as config_file:
    #     config = yaml.load(config_file)

    # # Create a place to track any indices that are deleted.
    # deleted_indices = {}

    # # We can define multiple Elasticsearch clusters to manage, so we'll have
    # # an outer loop for working through them.
    # for cluster_config in config:
    #     cluster_name = cluster_config['name']
    #     deleted_indices[cluster_name] = []

    #     # Create a collection to the cluster. We're using mangaged clusters in
    #     # Elastic Cloud for this example, so we can enable SSL security.
    #     es = Elasticsearch(cluster_config['endpoint'], use_ssl=True,
    #                        verify_certs=True, ca_certs=certifi.where())

    #     # Now we'll work through each set of time-series indices defined in
    #     # our config for this cluster.
    #     for index in cluster_config['indices']:
    #         prefix = index['prefix']
    #         print('Checking "%s" indices on %s cluster.' %
    #               (prefix, cluster_name))

    #         # Fetch all the index names.
    #         index_list = curator.IndexList(es)
    #         try:
    #             # Reduce the list to those that match the prefix.
    #             index_list.filter_by_regex(kind='prefix', value=prefix)
    #             # Reduce again, by age.
    #             index_list.filter_by_age(source='name', direction='older',
    #                               timestring='%Y.%m.%d', unit='days',
    #                               unit_count=index['days'])
    #             curator.DeleteIndices(index_list).do_action()
    #         # If nothing is left in the list, we'll get a NoIndices exception.
    #         # That's OK.
    #         except NoIndices:
    #             pass

    #         # Record the names of any indices we removed.
    #         deleted_indices[cluster_name].extend(index_list.working_list())

    # lambda_response = {'deleted': deleted_indices}
    # print(lambda_response)
    return {'hi': 'hi'}
