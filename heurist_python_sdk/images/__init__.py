from typing import Optional, TypedDict, Union

import aiohttp

from ..resource import APIResource
from ..utils import generate_random_hex


class ImageGenerateParams(TypedDict, total=False):
    model: str
    prompt: str
    neg_prompt: Optional[str]
    num_iterations: Optional[int]
    guidance_scale: Optional[float]
    width: Optional[int]
    height: Optional[int]
    seed: Optional[Union[int, str]]
    job_id_prefix: Optional[str]


class Image(ImageGenerateParams, total=False):
    url: str


ImagesResponse = Image
ImageModel = str


class Images(APIResource):
    async def generate(self, params: ImageGenerateParams) -> ImagesResponse:
        try:
            id = generate_random_hex(10)

            model = params["model"]
            prompt = params.get("prompt", "")
            neg_prompt = params.get("neg_prompt")
            num_iterations = params.get("num_iterations")
            guidance_scale = params.get("guidance_scale")
            width = params.get("width")
            height = params.get("height")
            seed = params.get("seed")
            job_id_prefix = params.get("job_id_prefix", "sdk-image")

            prompt_text = prompt

            if model == "Zeek":
                prompt_text = prompt_text.replace("Zeek", "z33k").replace(
                    "zeek", "z33k"
                )
            elif model == "Philand":
                prompt_text = prompt_text.replace("Philand", "ph1land").replace(
                    "philand", "ph1land"
                )

            model_input = {"prompt": prompt_text}

            if neg_prompt is not None:
                model_input["neg_prompt"] = neg_prompt
            if num_iterations is not None:
                model_input["num_iterations"] = num_iterations
            if guidance_scale is not None:
                model_input["guidance_scale"] = guidance_scale
            if width is not None:
                model_input["width"] = width
            if height is not None:
                model_input["height"] = height
            if seed is not None:
                seed_int = int(seed)
                if seed_int > 9007199254740991:  # Number.MAX_SAFE_INTEGER
                    seed_int = seed_int % 9007199254740991
                model_input["seed"] = seed_int

            params = {
                "job_id": f"{job_id_prefix}-{id}",
                "model_input": {"SD": model_input},
                "model_type": "SD",
                "model_id": model,
                "deadline": 30,
                "priority": 1,
            }

            path = f"{self._client.baseURL}/submit_job"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    path,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._client.apiKey}",
                    },
                    json=params,
                ) as response:
                    if not response.ok:
                        if str(response.status).startswith(("4", "5")):
                            raise Exception(
                                "Generate image error. Please try again later"
                            )
                        raise Exception(f"HTTP error! status: {response.status}")

                    url = await response.text()
                    data_url = url.strip('"')

                    return {"url": data_url, "model": model, **model_input}

        except Exception as error:
            print(f"{str(error)}, generate image error")
            raise Exception(
                str(error) or "Generate image error. Please try again later"
            )
