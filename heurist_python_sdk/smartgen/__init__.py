import json
import re
from typing import Any, Dict, List, Optional, TypedDict, Union

from openai import AsyncOpenAI

from ..resource import APIResource


class SmartGenParams(TypedDict, total=False):
    description: str  # description of the image like "a dog chasing a boy"
    width: Optional[int]
    height: Optional[int]
    image_model: Optional[str]  # default: FLUX.1-dev
    language_model: Optional[str]  # default: nvidia/llama-3.1-nemotron-70b-instruct
    is_sd: Optional[bool]  # true if we want to use stable diffusion prompt format
    # fmt: off
    must_include: Optional[str]  # this word/phrase will be always included in the prompt
    # fmt: on
    examples: Optional[List[str]]  # example prompt(s)
    negative_prompt: Optional[str]  # only applies to SD
    quality: Optional[str]  # 'normal' | 'high', 20/30 iterations
    num_iterations: Optional[int]  # if specified, overrides quality setting
    guidance_scale: Optional[float]
    stylization_level: Optional[int]  # 1-5
    detail_level: Optional[int]  # 1-5
    color_level: Optional[int]  # 1-5
    lighting_level: Optional[int]  # 1-5
    param_only: Optional[bool]  # default is false


class CreatePromptParams(TypedDict, total=False):
    description: str
    is_sd: Optional[bool]
    language_model: Optional[str]
    must_include: Optional[str]
    examples: Optional[List[str]]
    stylization_level: Optional[int]
    detail_level: Optional[int]
    color_level: Optional[int]
    lighting_level: Optional[int]


class SmartGen(APIResource):
    def __init__(self, client):
        super().__init__(client)
        apiKey = self._client.apiKey
        if not apiKey:
            raise ValueError(
                "HEURIST_API_KEY environment variable is required for SmartGen"
            )

        self.openai = AsyncOpenAI(
            api_key=apiKey, base_url="https://llm-gateway.heurist.xyz"
        )

    def _validate_dimension_level(self, level: Optional[int]) -> Optional[int]:
        if level is None:
            return None
        return min(max(round(level), 1), 5)

    async def generate_image(
        self, params: SmartGenParams
    ) -> Union[Dict[str, Any], Dict[str, Union[str, Dict[str, Any]]]]:
        # Set defaults matching TypeScript exactly
        description = params["description"]
        width = params.get("width", 512)
        height = params.get("height", 512)
        image_model = params.get("image_model", "FLUX.1-dev")
        language_model = params.get(
            "language_model", "nvidia/llama-3.1-nemotron-70b-instruct"
        )
        is_sd = params.get("is_sd", False)
        must_include = params.get("must_include")
        examples = params.get("examples")
        negative_prompt = params.get(
            "negative_prompt", "(worst quality: 1.4), bad quality, nsfw"
        )
        quality = params.get("quality", "normal")
        num_iterations = params.get("num_iterations")
        guidance_scale = params.get("guidance_scale")
        stylization_level = params.get("stylization_level")
        detail_level = params.get("detail_level")
        color_level = params.get("color_level")
        lighting_level = params.get("lighting_level")
        param_only = params.get("param_only", False)

        # Prepare LLM prompt
        enhanced_prompt = await self._enhance_prompt(
            {
                "description": description,
                "is_sd": is_sd,
                "must_include": must_include,
                "examples": examples,
                "language_model": language_model,
                "stylization_level": self._validate_dimension_level(stylization_level),
                "detail_level": self._validate_dimension_level(detail_level),
                "color_level": self._validate_dimension_level(color_level),
                "lighting_level": self._validate_dimension_level(lighting_level),
            }
        )

        # Calculate iterations
        iterations = (
            num_iterations
            if num_iterations is not None
            else (30 if quality == "high" else 20)
        )

        # Prepare generation parameters
        generation_params = {
            "model": image_model,
            "width": width,
            "height": height,
            "prompt": enhanced_prompt,
            "num_iterations": iterations,
            "guidance_scale": (
                guidance_scale if guidance_scale is not None else (6 if is_sd else 3)
            ),
        }

        if is_sd:
            generation_params["neg_prompt"] = negative_prompt

        # Return just parameters if param_only is true
        if param_only:
            return {"parameters": generation_params}

        # Generate the image
        try:
            response = await self._client.images.generate(generation_params)
            return {"url": response["url"], "parameters": generation_params}
        except Exception as error:
            print("Image generation failed:", str(error))
            raise Exception(f"Failed to generate image: {str(error)}")

    def _create_system_prompt(self) -> str:
        return (
            "You are an expert in writing prompts for AI art generation. You excel at "
            "creating detailed and creative visual descriptions. Maintain consistent style "
            "and tone. Incorporating specific elements naturally. Learn from examples when "
            "provided. Always aim for clear, descriptive language that paints a creative picture."
        )

    def _get_dimension_guideline(
        self, level: Optional[int], dimension_type: str
    ) -> Optional[str]:
        if level is None:
            return None

        valid_level = min(max(round(level), 1), 5)

        guidelines = {
            "stylization": {
                "description": (
                    "On a scale 1~5 Controls the balance between realism and stylization\n"
                    "1: Photorealistic - true-to-life\n"
                    "2: High realism with slight artistic touch\n"
                    "3: Balanced blend of realism and artistic style\n"
                    "4: Clearly stylized art\n"
                    "5: Highly abstract/artistic interpretation"
                )
            },
            "detail": {
                "description": (
                    "On a scale 1~5 Controls the level of detail and intricacy\n"
                    "1: Minimalist, essential elements only\n"
                    "2: Clean and simple\n"
                    "3: Balanced detail level\n"
                    "4: Rich in details\n"
                    "5: Extremely intricate, hyper-detailed"
                )
            },
            "color": {
                "description": (
                    "On a scale 1~5 Controls color intensity and saturation\n"
                    "1: Monochromatic/grayscale\n"
                    "2: Muted, subdued colors\n"
                    "3: Natural, true-to-life colors\n"
                    "4: Enhanced vibrancy\n"
                    "5: Hyper-saturated, intense colors"
                )
            },
            "lighting": {
                "description": (
                    "On a scale 1~5 Controls lighting intensity and contrast\n"
                    "1: Flat, even lighting\n"
                    "2: Soft, diffused illumination\n"
                    "3: Natural, balanced lighting\n"
                    "4: High contrast, dramatic lighting\n"
                    "5: Extreme dramatic lighting"
                )
            },
        }

        dimension_map = {
            "stylization": "stylization",
            "detail": "detail",
            "color": "color",
            "lighting": "lighting",
        }

        dimension = dimension_map.get(dimension_type)
        if not dimension:
            return None
        if valid_level == 3:
            return None

        return (
            f"Dimension {dimension_type.upper()}:\n"
            f"{guidelines[dimension]['description']}\n\n"
            f"We want to create a prompt with {dimension_type} level {valid_level}. "
            f"Think carefully. Naturally integrate this aspect into your final prompt "
            f"without explicitly mentioning the level number."
        )

    def _create_flux_user_prompt(self, params: CreatePromptParams) -> str:
        description = params["description"]
        must_include = params.get("must_include")
        examples = params.get("examples")
        stylization_level = params.get("stylization_level")
        detail_level = params.get("detail_level")
        color_level = params.get("color_level")
        lighting_level = params.get("lighting_level")

        prompt = f"""Create a detailed visual prompt following these guidelines:

KEY REQUIREMENTS:
- The prompt describes the contents and styles of the image. Don't say "create an image of ..." but just write the description.
- Keep the final prompt under 50 words
- Focus on visual elements and composition
- Be direct and straightforward
- Avoid metaphors or "like" comparisons
- Integrate technical terms in photography or digital illustration

CORE IMAGE DESCRIPTION:
"{description}"
"""

        if must_include:
            prompt += f'\nREQUIRED ELEMENTS:\nMust include this description without altering the texts: "{must_include}"'

        if examples:
            prompt += (
                "\nPROMPT FORMAT REFERENCE:\nExample prompt(s) to match format: "
                + "\n".join(f"{i+1}. {example}" for i, example in enumerate(examples))
            )

        dimensions = [
            self._get_dimension_guideline(stylization_level, "stylization"),
            self._get_dimension_guideline(detail_level, "detail"),
            self._get_dimension_guideline(color_level, "color"),
            self._get_dimension_guideline(lighting_level, "lighting"),
        ]
        dimensions = [d for d in dimensions if d]

        if dimensions:
            prompt += (
                "\n\nYou should integrate descriptions about style dimensions in a natural way "
                "NEVER explicitly mention level number. NEVER say X/Y or Level X or dimension:X. "
                "NEVER copy guideline language. Let the dimension influence your word choice and "
                "descriptive style rather than listing them directly. Treat them as creative "
                "inspiration rather than technical requirements.\n"
                + "\n\n".join(dimensions)
            )

        prompt += "\n\nReturn only the final prompt without any explanations or quotes. Ensure all specified aspects are implemented accurately."
        return prompt

    def _create_stable_diffusion_user_prompt(self, params: CreatePromptParams) -> str:
        description = params["description"]
        must_include = params.get("must_include")
        examples = params.get("examples")
        stylization_level = params.get("stylization_level")
        detail_level = params.get("detail_level")
        color_level = params.get("color_level")
        lighting_level = params.get("lighting_level")

        prompt = f"""Create a detailed visual prompt following these guidelines:

- Structure: comma-separated descriptive words and phrases only
- Length: maximum 15 tags
- How to emphasis a keyword: use a tag like (keyword) or (keyword:1.2) for slight boost, (keyword:1.4) for strong boost. Never boost above 1.4.
- Core elements first: subject, style, lighting, composition
- Avoid complete sentences, action words (use, make, create), or metaphors
- Be descriptive and straightforward and creative

CORE IMAGE DESCRIPTION:
"{description}"
"""

        if must_include:
            prompt += f'\nREQUIRED ELEMENTS:\nMust include this description without altering the texts: "{must_include}"'

        if examples:
            prompt += (
                "\nPROMPT FORMAT REFERENCE:\nExample prompt(s) to match format: "
                + "\n".join(examples)
            )

        dimensions = [
            self._get_dimension_guideline(stylization_level, "stylization"),
            self._get_dimension_guideline(detail_level, "detail"),
            self._get_dimension_guideline(color_level, "color"),
            self._get_dimension_guideline(lighting_level, "lighting"),
        ]
        dimensions = [d for d in dimensions if d]

        if dimensions:
            prompt += (
                "\n\nYou should integrate descriptions about style dimensions in a natural way "
                "NEVER explicitly mention level number. NEVER say X/Y or Level X or dimension:X. "
                "NEVER copy guideline language. Let the dimension influence your word choice and "
                "descriptive style rather than listing them directly. Treat them as creative "
                "inspiration rather than technical requirements.\n"
                + "\n\n".join(dimensions)
            )

        prompt += "\n\nReturn only the final prompt without any explanations or quotes. Ensure all specified aspects are implemented accurately."
        return prompt

    async def _enhance_prompt(self, params: CreatePromptParams) -> str:
        try:
            messages = [
                {"role": "system", "content": self._create_system_prompt()},
                {
                    "role": "user",
                    "content": (
                        self._create_stable_diffusion_user_prompt(params)
                        if params.get("is_sd")
                        else self._create_flux_user_prompt(params)
                    ),
                },
            ]

            completion = await self.openai.chat.completions.create(
                model=params.get("language_model", "mistralai/mixtral-8x7b-instruct"),
                messages=messages,
                temperature=0.7,
                max_tokens=200,
            )

            raw_prompt = (
                completion.choices[0].message.content.strip()
                if completion.choices
                else params["description"]
            )
            return self._clean_prompt(raw_prompt)

        except Exception as error:
            print("Failed to enhance prompt:", str(error))
            return params["description"]

    def _clean_prompt(self, prompt: str) -> str:
        try:
            # Clean control characters
            prompt = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", prompt)

            if prompt.startswith("[") or prompt.startswith("{"):
                try:
                    parsed = json.loads(prompt)
                    if isinstance(parsed, list):
                        prompt = (
                            parsed[0].get("message", {}).get("content", "").strip()
                            or prompt
                        )
                    elif (
                        isinstance(parsed, dict)
                        and "message" in parsed
                        and "content" in parsed["message"]
                    ):
                        prompt = parsed["message"]["content"].strip()
                    elif isinstance(parsed, str):
                        prompt = parsed.strip()
                except json.JSONDecodeError:
                    content_match = re.search(r'"content":\s*"([^"]+)"', prompt)
                    if content_match:
                        prompt = content_match.group(1)

            # Clean remaining artifacts
            prompt = (
                prompt.strip("\"' \t\n\r")
                .replace("\\n", " ")
                .replace('\\"', '"')
                .replace(";", ",")
            )
            prompt = re.sub(r"\s+", " ", prompt)

            return prompt
        except Exception as e:
            print("Error cleaning prompt:", str(e))
            return prompt
