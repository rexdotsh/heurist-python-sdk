import asyncio
from enum import Enum
from random import Random
from typing import Any, Dict, Optional, TypedDict

import aiohttp

from ..resource import APIResource
from ..utils import generate_random_hex


def parse_api_key_string(combined_key: str) -> Dict[str, str]:
    consumer_id, api_key = (
        combined_key.split("#", 1) if "#" in combined_key else ("", combined_key)
    )
    return {"consumerId": consumer_id, "apiKey": api_key}


class WorkflowTaskType(str, Enum):
    Upscaler = "upscaler"
    FluxLora = "flux-lora"
    Text2Video = "txt2vid"


class WorkflowTaskOptions(TypedDict, total=False):
    consumerId: Optional[str]
    job_id_prefix: Optional[str]
    timeout_seconds: Optional[int]
    workflow_id: Optional[str]
    apiKey: Optional[str]


class WorkflowTask:
    def __init__(self, options: WorkflowTaskOptions):
        self.consumerId = options.get("consumerId")
        self.job_id_prefix = options.get("job_id_prefix")
        self.timeout_seconds = options.get("timeout_seconds")
        self.workflow_id = options.get("workflow_id")
        self.apiKey = options.get("apiKey")

    @property
    def task_type(self) -> WorkflowTaskType:
        raise NotImplementedError()

    @property
    def task_details(self) -> Dict[str, Any]:
        raise NotImplementedError()


class UpscalerTaskOptions(WorkflowTaskOptions):
    image_url: str


class UpscalerTask(WorkflowTask):
    def __init__(self, options: UpscalerTaskOptions):
        super().__init__(options)
        self.image_url = options["image_url"]

    @property
    def task_type(self) -> WorkflowTaskType:
        return WorkflowTaskType.Upscaler

    @property
    def task_details(self) -> Dict[str, Any]:
        return {"parameters": {"image": self.image_url}}


class FluxLoraTaskOptions(WorkflowTaskOptions):
    prompt: str
    aspect_ratio: Optional[str]
    width: Optional[int]
    height: Optional[int]
    guidance: Optional[float]
    steps: Optional[int]
    lora_name: str


class FluxLoraTask(WorkflowTask):
    def __init__(self, options: FluxLoraTaskOptions):
        super().__init__(options)
        self.prompt = options["prompt"]
        self.aspect_ratio = options.get("aspect_ratio", "custom")
        self.width = options.get("width", 1024)
        self.height = options.get("height", 1024)
        self.guidance = options.get("guidance", 6)
        self.steps = options.get("steps", 20)
        self.lora_name = options["lora_name"]

    @property
    def task_type(self) -> WorkflowTaskType:
        return WorkflowTaskType.FluxLora

    @property
    def task_details(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "prompt": self.prompt,
                "aspect_ratio": self.aspect_ratio,
                "width": self.width,
                "height": self.height,
                "guidance": self.guidance,
                "steps": self.steps,
                "lora_name": self.lora_name,
            }
        }


class Text2VideoTaskOptions(WorkflowTaskOptions):
    prompt: str
    width: Optional[int]
    height: Optional[int]
    length: Optional[int]
    steps: Optional[int]
    seed: Optional[int]
    fps: Optional[int]
    quality: Optional[int]


class Text2VideoTask(WorkflowTask):
    def __init__(self, options: Text2VideoTaskOptions):
        super().__init__(options)
        self.prompt = options["prompt"]
        self.width = options.get("width", 848)
        self.height = options.get("height", 480)
        self.length = options.get("length", 37)
        self.steps = options.get("steps", 30)
        self.seed = options.get(
            "seed", int.from_bytes(Random().randbytes(8), "big") % (2**53 - 1)
        )
        self.fps = options.get("fps", 24)
        self.quality = options.get("quality", 80)

    @property
    def task_type(self) -> WorkflowTaskType:
        return WorkflowTaskType.Text2Video

    @property
    def task_details(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "prompt": self.prompt,
                "width": self.width,
                "height": self.height,
                "length": self.length,
                "steps": self.steps,
                "seed": self.seed,
                "fps": self.fps,
                "quality": self.quality,
            }
        }


class WorkflowTaskResult(TypedDict):
    task_id: str
    status: str  # 'waiting' | 'running' | 'finished' | 'failed' | 'canceled'
    result: Optional[Any]


class Workflow(APIResource):
    def __init__(self, client):
        super().__init__(client)
        parsed = parse_api_key_string(self._client.apiKey)
        self.defaultConsumerId = parsed["consumerId"]
        self.defaultApiKey = parsed["apiKey"]

    async def execute_workflow(self, task: WorkflowTask) -> str:
        await self.resource_request(task.consumerId or self.defaultConsumerId)
        task_id = await self.create_task(task)
        return task_id

    async def query_task_result(self, task_id: str) -> WorkflowTaskResult:
        url = f"{self._client.workflowURL}/task_result_query"
        headers = {"Content-Type": "application/json"}
        data = {"task_id": task_id, "apiKey": self.defaultApiKey}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if not response.ok:
                    raise Exception(f"Task result query failed: {response.reason}")
                return await response.json()

    async def resource_request(self, consumer_id: str) -> str:
        url = f"{self._client.workflowURL}/resource_request"
        headers = {"Content-Type": "application/json"}
        data = {"consumer_id": consumer_id, "apiKey": self.defaultApiKey}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if not response.ok:
                    raise Exception(f"Resource request failed: {response.reason}")
                result = await response.json()
                return result["miner_id"]

    async def create_task(self, task: WorkflowTask) -> str:
        url = f"{self._client.workflowURL}/task_create"
        headers = {"Content-Type": "application/json"}
        job_id_prefix = task.job_id_prefix or "sdk-workflow"
        id = generate_random_hex(10)
        job_id = f"{job_id_prefix}-{id}"

        # Apply default values
        task.consumerId = task.consumerId or self.defaultConsumerId
        task.apiKey = task.apiKey or self.defaultApiKey

        data: Dict[str, Any] = {
            "job_id": job_id,
            "task_type": task.task_type,
            "consumer_id": task.consumerId,
            "apiKey": task.apiKey,
            **task.task_details,
        }

        if task.workflow_id:
            data["workflow_id"] = task.workflow_id
        if task.timeout_seconds:
            data["timeout_seconds"] = task.timeout_seconds

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if not response.ok:
                    raise Exception(f"Task creation failed: {response.reason}")
                result = await response.json()
                return result["task_id"]

    async def execute_workflow_and_wait_for_result(
        self, task: WorkflowTask, timeout: int = 300000, interval: int = 10000
    ) -> WorkflowTaskResult:
        if interval < 1000:
            raise Exception("Interval should be more than 1000 (1 second)")

        task_id = await self.execute_workflow(task)
        start_time = asyncio.get_event_loop().time() * 1000  # Convert to milliseconds

        while True:
            result = await self.query_task_result(task_id)
            if result["status"] in ["finished", "failed"]:
                return result

            if (asyncio.get_event_loop().time() * 1000) - start_time > timeout:
                raise Exception("Timeout waiting for task result")

            await asyncio.sleep(interval / 1000)  # Convert milliseconds to seconds

    async def cancel_task(self, task_id: str) -> Dict[str, str]:
        url = f"{self._client.workflowURL}/task_cancel"
        headers = {"Content-Type": "application/json"}
        data = {"task_id": task_id, "apiKey": self.defaultApiKey}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if not response.ok:
                    raise Exception(f"Task cancellation failed: {response.reason}")
                result = await response.json()
                return {"task_id": result["task_id"], "msg": result["msg"]}
