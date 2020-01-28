import pytest
import copy
import os

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import ENDPOINT
from utils import change_uuids, read_test_config

LinuxEndpointPayload = read_test_config(file_name="linux_endpoint_payload.json")
WindowsEndpointPayload = read_test_config(file_name="windows_endpoint_payload.json")
HTTPEndpointPayload = read_test_config(file_name="http_endpoint_payload.json")


class TestExecTasks:
    @pytest.mark.runbook
    @pytest.mark.endpoint
    @pytest.mark.parametrize('EndpointPayload', [LinuxEndpointPayload, WindowsEndpointPayload, HTTPEndpointPayload])
    def test_endpoint_crud(self, EndpointPayload):
        """
        test_linux_endpoint_create_with_required_fields, test_linux_endpoint_update, test_linux_endpoint_delete
        test_windows_endpoint_create_with_required_fields, test_windows_endpoint_update, test_windows_endpoint_delete
        test_http_endpoint_create_with_auth, test_http_endpoint_update, test_http_endpoint_delete
        """

        client = get_api_client()
        endpoint = change_uuids(EndpointPayload, {})

        # Endpoint Create
        res, err = client.endpoint.create(endpoint)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_uuid = ep["metadata"]["uuid"]
        ep_name = ep["spec"]["name"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"

        # Endpoint Read
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_uuid == ep["metadata"]["uuid"]
        assert ep_state == "ACTIVE"
        assert ep_name == ep["spec"]["name"]

        # Endpoint Update
        ep_type = ep["spec"]["resources"]["type"]
        del ep["status"]
        if ep_type == ENDPOINT.TYPES.HTTP:
            ep["spec"]["resources"]["attrs"]["url"] = "new_updated_url"
        elif ep_type == ENDPOINT.TYPES.LINUX or ep_type == ENDPOINT.TYPES.WINDOWS:
            ep["spec"]["resources"]["attrs"]["values"] = ["1.1.1.1", "2.2.2.2"]
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        res, err = client.endpoint.update(ep_uuid, ep)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        ep = res.json()
        ep_state = ep["status"]["state"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"
        if ep_type == ENDPOINT.TYPES.HTTP:
            assert ep["spec"]["resources"]["attrs"]["url"] == "new_updated_url"
        elif ep_type == ENDPOINT.TYPES.LINUX or ep_type == ENDPOINT.TYPES.WINDOWS:
            assert "1.1.1.1" in ep["spec"]["resources"]["attrs"]["values"]
            assert "2.2.2.2" in ep["spec"]["resources"]["attrs"]["values"]
            assert len(ep["spec"]["resources"]["attrs"]["values"]) == 2
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        # download the endpoint
        file_path = client.endpoint.export_file(ep_uuid, passphrase="test_passphrase")

        '''
        # upload the endpoint
        res, err = client.endpoint.import_file(ep_uuid + '.json', ep_name + "-uploaded",
                                               ep["metadata"].get("project_reference", {}).get("uuid", ""),
                                               passphrase="test_passphrase")
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        uploaded_ep = res.json()
        uploaded_ep_state = uploaded_ep["status"]["state"]
        uploaded_ep_uuid = uploaded_ep["metadata"]["uuid"]
        assert uploaded_ep_state == "ACTIVE"

        # delete uploaded endpoint
        _, err = client.endpoint.delete(uploaded_ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("uploaded endpoint deleted")
        '''

        # delete downloaded file
        os.remove(file_path)

        # delete the endpoint
        _, err = client.endpoint.delete(ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("endpoint {} deleted".format(ep_name))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_state == "DELETED"

    @pytest.mark.runbook
    @pytest.mark.endpoint
    @pytest.mark.parametrize('EndpointPayload', [LinuxEndpointPayload, WindowsEndpointPayload])
    def test_endpoint_validation_and_type_update(self, EndpointPayload):
        """
        test_endpoint_update_windows_to_http, test_endpoint_update_linux_to_http
        test_linux_endpoint_create_without_required_fields, test_windows_endpoint_create_without_required_fields
        test_http_endpoint_create_without_auth
        """

        client = get_api_client()
        endpoint = copy.deepcopy(change_uuids(EndpointPayload, {}))

        # set values and credentials to empty
        endpoint['spec']['resources']['attrs']['values'] = []
        endpoint['spec']['resources']['attrs']['credential_definition_list'][0]['username'] = ''
        endpoint['spec']['resources']['attrs']['credential_definition_list'][0]['secret']['value'] = ''

        # Endpoint Create
        res, err = client.endpoint.create(endpoint)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_uuid = ep["metadata"]["uuid"]
        ep_name = ep["spec"]["name"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "DRAFT"

        # Checking validation errors
        assert len(ep["status"]["message_list"]) > 0
        validations = ""
        for message in ep["status"]["message_list"]:
            validations += message["message"]
        assert "Endpoint values cannot be empty" in validations
        cred = ep["status"]["resources"]["attrs"]['credential_definition_list'][0]
        assert len(ep["status"]["message_list"]) > 0
        for message in cred["message_list"]:
            validations += message["message"]
        assert "Username is a required field" in validations
        assert "Secret value for credential is empty" in validations

        # update endpoint type
        ep["spec"]["resources"]["type"] = ENDPOINT.TYPES.HTTP
        ep["spec"]["resources"]["attrs"] = {"url": "test_url", "authentication": {"type": "none"}}
        del ep["status"]

        res, err = client.endpoint.update(ep_uuid, ep)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        ep = res.json()
        ep_state = ep["status"]["state"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"
        assert ep["spec"]["resources"]["type"] == ENDPOINT.TYPES.HTTP

        # delete the endpoint
        _, err = client.endpoint.delete(ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("endpoint {} deleted".format(ep_name))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_state == "DELETED"

    @pytest.mark.runbook
    @pytest.mark.endpoint
    @pytest.mark.parametrize('EndpointPayload', [HTTPEndpointPayload])
    def test_http_endpoint_validation_and_update(self, EndpointPayload):
        """
        test_http_endpoint_create_without_required_fields,
        test_endpoint_update_http_to_linux
        """

        client = get_api_client()
        endpoint = copy.deepcopy(change_uuids(EndpointPayload, {}))

        # setting url to empty
        endpoint['spec']['resources']['attrs']['url'] = ''

        # Endpoint Create
        res, err = client.endpoint.create(endpoint)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_uuid = ep["metadata"]["uuid"]
        ep_name = ep["spec"]["name"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "DRAFT"

        # Checking validation errors
        assert len(ep["status"]["message_list"]) > 0
        validations = ""
        for message in ep["status"]["message_list"]:
            validations += message["message"]
        assert "URL is a required field" in validations

        LinuxAttrs = change_uuids(LinuxEndpointPayload["spec"]["resources"]["attrs"], {})

        # update endpoint type
        ep["spec"]["resources"]["type"] = ENDPOINT.TYPES.LINUX
        ep["spec"]["resources"]["attrs"] = LinuxAttrs
        del ep["status"]

        res, err = client.endpoint.update(ep_uuid, ep)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        ep = res.json()
        ep_state = ep["status"]["state"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"
        assert ep["spec"]["resources"]["type"] == ENDPOINT.TYPES.LINUX

        # delete the endpoint
        _, err = client.endpoint.delete(ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("endpoint {} deleted".format(ep_name))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_state == "DELETED"
