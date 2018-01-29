#!/usr/bin/env python
import os
import sys
import unittest
from copy import deepcopy
import yaml
from app import ESException, ESCleanup
import datetime


class TestApp(unittest.TestCase):

    with open(os.environ['ES_IDX_MANAGER_SETTINGS'], 'r') as config_file:
        config = yaml.load(config_file)

    for cluster_config in config:
        if cluster_config["name"] == "test configuration":
            test_config = cluster_config

    es = ESCleanup(None, None, test_config)

    def test_deletion_rule(self):
        index_format = self.test_config["index_format"]

        # Should not delete index from today
        today_index_name = "test-" + datetime.datetime.today().strftime(index_format)
        today_index = {"index": today_index_name}
        self.assertEqual(self.es.should_delete_index(today_index), False)

        # Should not delete index from 6 days ago
        days_to_subtract = int(self.test_config.get('days')) - 1
        recent_index_name = "test-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        recent_index = {"index": recent_index_name}
        self.assertEqual(self.es.should_delete_index(recent_index), False)

        # Should not delete kibana index
        kibana_index = {"index": ".kibana"}
        self.assertEqual(self.es.should_delete_index(kibana_index), False)

        # Should delete index from 7 days ago
        days_to_subtract = int(self.test_config.get('days'))
        old_index_name = "test-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        old_index = {"index": old_index_name}
        self.assertEqual(self.es.should_delete_index(old_index), True)

    def test_index_deletion_pipeline(self):
        # create 10 test indices backdating from today into the past
        index_format = self.test_config["index_format"]
        indices_to_cleanup = []
        for subtract in range(0, 10):
            index_name = "test-" + (datetime.date.today() - datetime.timedelta(days=subtract)).strftime(index_format)
            self.es.create_index(index_name)
            # store indices that are recent within 7 days to cleanup at the end
            if subtract < 7:
                indices_to_cleanup.append(index_name)

        # Store indices before/after management of indices and ensure 3 were deleted
        pre_managed_indices_len = len(self.es.get_indices())
        self.es.manage_indices()
        post_managed_indices_len = len(self.es.get_indices())
        self.assertEqual(pre_managed_indices_len - 3, post_managed_indices_len)

        # deletion of 7 indices that were created but not deleted above
        for index_name in indices_to_cleanup:
            self.es.delete_index(index_name)


if __name__ == '__main__':
    unittest.main()
