from typing import Optional, Union

from . import apis
from .lib import read_env


class ClientOptions:
    def __init__(
        self,
        baseURL: Optional[str] = None,
        workflowURL: Optional[str] = None,
        apiKey: Optional[str] = None,
    ):
        self.baseURL = baseURL
        self.workflowURL = workflowURL
        self.apiKey = apiKey


class Heurist:
    def __init__(self, options: Optional[Union[ClientOptions, dict]] = None):
        if isinstance(options, dict):
            options = ClientOptions(**options)
        elif options is None:
            options = ClientOptions()

        baseURL = options.baseURL or read_env("HEURIST_BASE_URL")
        workflowURL = options.workflowURL or read_env("HEURIST_WORKFLOW_URL")
        apiKey = options.apiKey or read_env("HEURIST_API_KEY")

        if apiKey is None:
            raise ValueError(
                "The HEURIST_API_KEY environment variable is missing or empty; either provide it, "
                "or instantiate the Heurist client with an apiKey option, like "
                "Heurist({'apiKey': 'My API Key'}) or Heurist(ClientOptions(apiKey='My API Key'))."
            )

        self.baseURL = baseURL or "http://sequencer.heurist.xyz"
        self.workflowURL = workflowURL
        self.apiKey = apiKey

        self.images = apis.Images(self)
        self.workflow = apis.Workflow(self)
        self.smartgen = apis.SmartGen(self)
