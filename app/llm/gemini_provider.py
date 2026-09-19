from google import genai
from google.genai import types


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        temperature: float = 0.1,
        max_output_tokens: int = 1200,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        client = genai.Client(api_key=self._api_key)
        async with client.aio as aclient:
            response = await aclient.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                ),
            )

        text = response.text or ""
        return text.strip()
