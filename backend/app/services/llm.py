import os
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any

# Import pi-coding-agent modules
from pi_agent.agent import Agent, AgentConfig
from pi_agent.sandbox import Sandbox
from pi_agent.tools.registry import ToolRegistry
from pi_agent.llm import build_provider, OpenAIProvider, NeutralMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, system_prompt: str, messages: List[Dict[str, str]]) -> Tuple[str, str, str]:
        """
        Generates an LLM response.
        Returns: (response_text, provider_name, model_name)
        """
        pass

    @abstractmethod
    def generate_streamed_response(self, system_prompt: str, messages: List[Dict[str, str]], on_event: callable) -> Tuple[str, str, str]:
        """
        Generates an LLM response with streaming events.
        """
        pass

def check_native_tool_support(provider_type: str, model: str, base_url: str = "") -> bool:
    """
    Checks whether the target provider and model natively support function/tool calling.
    llama3 (base) does not have tool calling templates and returns HTTP 400 if tools are sent.
    """
    if provider_type in ["cloud", "anthropic", "openrouter"]:
        return True
        
    model_lower = (model or "").lower()
    # Base Llama 3 models in Ollama do not have tool calling templates in their Modelfile
    if model_lower == "llama3" or model_lower.startswith("llama3:") or "llama3:latest" in model_lower:
        return False
    if any(m in model_lower for m in ["llama3.1", "llama3.2", "llama3.3", "qwen2.5", "qwen3", "mistral"]):
        return True

    # Probe Ollama capabilities via /api/show if reachable
    try:
        import httpx
        show_url = base_url.replace("/v1/", "").replace("/v1", "").rstrip("/") + "/api/show"
        with httpx.Client(timeout=1.5) as client:
            resp = client.post(show_url, json={"model": model})
            if resp.status_code == 200:
                data = resp.json()
                caps = data.get("capabilities", [])
                template = data.get("template", "")
                if "tools" in caps or "{{ .Tools }}" in template or "{{.Tools}}" in template:
                    return True
                return False
    except Exception:
        pass

    return False

def is_writing_request(text: str) -> bool:
    """Detects whether a user prompt requests creating a formal essay, document, or artifact."""
    if not text:
        return False
    t = text.lower()
    writing_keywords = [
        "essay", "write an essay", "article", "write an article",
        "draft a", "create a document", "write a guide", "create a guide",
        "checklist", "ship 30", "1,250", "1250", "write a blog",
        "create an html", "write html", "generate artifact", "create artifact",
        "produce an artifact", "writing skill"
    ]
    return any(kw in t for kw in writing_keywords)

class OllamaCompatibleProvider(OpenAIProvider):
    """
    OpenAI-compatible provider for Ollama that guarantees safety when interacting with
    models (such as llama3:latest) that do not support native OpenAI-format tool calling.
    
    When supports_tools is False, tool declarations are omitted from the payload so
    Ollama executes the standard conversational loop without returning HTTP 400.
    """
    def __init__(self, model: str, base_url: str, supports_tools: bool = False, max_tokens: Optional[int] = None):
        tokens = max_tokens or settings.CHAT_MAX_TOKENS
        super().__init__(model=model, api_key="ollama", base_url=base_url, max_tokens=tokens)
        self.supports_tools = supports_tools

    def _payload(
        self, system: str, messages: List[NeutralMessage], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        payload = super()._payload(system, messages, tools)
        if not self.supports_tools or not tools:
            payload.pop("tools", None)
            
        # Optional optimization: limit context size for Ollama to reduce latency, unless overridden.
        # Pass keep_alive via extra_body so OpenAI SDK completions.create accepts it without TypeError.
        payload.setdefault("extra_body", {})["keep_alive"] = "1h"
        return payload

class PiFrameworkProvider(LLMProvider):
    def __init__(self, provider_type: str, model: Optional[str] = None):
        self.provider_type = provider_type.lower()
        if self.provider_type == "cloud":
            # Guard against passing the provider name 'openrouter' as a model ID
            if not model or model.strip().lower() == "openrouter":
                self.model = settings.OPENROUTER_MODEL
            else:
                self.model = model.strip()
            api_key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY is not set.")
            self.pi_provider = build_provider(provider="openrouter", model=self.model, api_key=api_key)
            self.display_provider = "cloud (openrouter)"
            self.supports_tools = True
        elif self.provider_type == "anthropic":
            self.model = model or settings.ANTHROPIC_MODEL_NAME
            api_key = os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY is not set.")
            self.pi_provider = build_provider(provider="anthropic", model=self.model, api_key=api_key)
            self.display_provider = "cloud (anthropic)"
            self.supports_tools = True
        else:
            # Fallback to Ollama local
            if not model or model.strip().lower() in ["local", "ollama"]:
                self.model = settings.OLLAMA_MODEL_NAME
            else:
                self.model = model.strip()
            ollama_base_url = settings.OLLAMA_BASE_URL.rstrip('/')
            if not ollama_base_url.endswith("/v1"):
                ollama_v1 = f"{ollama_base_url}/v1/"
            else:
                ollama_v1 = f"{ollama_base_url}/"

            # Check if model is actually installed
            try:
                import httpx
                tags_url = ollama_base_url.replace("/v1", "") + "/api/tags"
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get(tags_url)
                    if resp.status_code == 200:
                        models = [m.get("name") for m in resp.json().get("models", [])]
                        # Account for tags like :latest
                        has_model = False
                        for m in models:
                            if m == self.model or m.startswith(self.model + ":") or self.model.startswith(m + ":"):
                                has_model = True
                                break
                            # If self.model has no tag, check if m starts with it
                            if ":" not in self.model and m.startswith(self.model + ":"):
                                has_model = True
                                break
                        if not has_model:
                            raise ValueError(f"Model '{self.model}' is not installed in Ollama. Please manually install it via 'ollama pull {self.model}'.")
            except httpx.RequestError:
                logger.warning("Could not connect to Ollama to check models.")
            except ValueError:
                raise

            self.supports_tools = check_native_tool_support(self.provider_type, self.model, ollama_base_url)
            self.pi_provider = OllamaCompatibleProvider(
                model=self.model,
                base_url=ollama_v1,
                supports_tools=self.supports_tools
            )
            self.display_provider = "local (ollama)"
            
    def generate_response(self, system_prompt: str, messages: List[Dict[str, str]]) -> Tuple[str, str, str]:
        agent_init_start = time.perf_counter()
        from app.services.writing import writing_tool
        config = AgentConfig(system_prompt=system_prompt)
        sandbox = Sandbox(".")
        
        last_msg = messages[-1] if messages else None
        user_input = last_msg.get("content", "") if last_msg else "Hello"
        is_writing = is_writing_request(user_input)
        
        # Configure output limits dynamically: sensible limits for ordinary chat and longer limits for essays
        target_max_tokens = settings.ESSAY_MAX_TOKENS if is_writing else settings.CHAT_MAX_TOKENS
        if hasattr(self.pi_provider, "max_tokens"):
            self.pi_provider.max_tokens = target_max_tokens

        # When native tool calling is supported:
        # For local providers, only register writing_tool if the request actually requires writing an artifact.
        # This prevents qwen3:4b from entering unnecessary tool calling loops and thinking hangs on normal chat.
        if self.supports_tools and (self.provider_type != "local" or is_writing):
            registry = ToolRegistry([writing_tool])
        else:
            registry = ToolRegistry([])
        
        # Format conversation history
        neutral_messages = []
        history = messages[:-1]
        
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            neutral_messages.append({"role": role, "content": content})
            
        agent = Agent(
            config=config, 
            provider=self.pi_provider, 
            registry=registry, 
            sandbox=sandbox, 
            messages=neutral_messages
        )
        agent_init_time = time.perf_counter() - agent_init_start
        logger.info(f"TIMING: [llm] Agent Init Latency: {agent_init_time:.4f}s")
        
        inference_start = time.perf_counter()
        try:
            response_text = agent.run(user_input)
        except Exception as e:
            logger.error(f"Pi Coding Agent failed: {e}")
            raise RuntimeError(f"Pi Agent execution failed: {e}") from e

        inference_time = time.perf_counter() - inference_start
        logger.info(f"TIMING: [llm] Inference Latency: {inference_time:.4f}s")

        return response_text, self.display_provider, self.model

    def generate_streamed_response(self, system_prompt: str, messages: List[Dict[str, str]], on_event: callable) -> Tuple[str, str, str]:
        agent_init_start = time.perf_counter()
        from app.services.writing import writing_tool
        config = AgentConfig(system_prompt=system_prompt, stream=True)
        sandbox = Sandbox(".")
        
        last_msg = messages[-1] if messages else None
        user_input = last_msg.get("content", "") if last_msg else "Hello"
        is_writing = is_writing_request(user_input)

        target_max_tokens = settings.ESSAY_MAX_TOKENS if is_writing else settings.CHAT_MAX_TOKENS
        if hasattr(self.pi_provider, "max_tokens"):
            self.pi_provider.max_tokens = target_max_tokens
        
        if self.supports_tools and (self.provider_type != "local" or is_writing):
            registry = ToolRegistry([writing_tool])
        else:
            registry = ToolRegistry([])
        
        neutral_messages = []
        history = messages[:-1]
        
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            neutral_messages.append({"role": role, "content": content})
            
        agent = Agent(
            config=config, 
            provider=self.pi_provider, 
            registry=registry, 
            sandbox=sandbox, 
            messages=neutral_messages
        )
        agent.on_event = on_event
        
        agent_init_time = time.perf_counter() - agent_init_start
        logger.info(f"TIMING: [llm] Agent Init Latency (streamed): {agent_init_time:.4f}s")
        
        inference_start = time.perf_counter()
        try:
            response_text = agent.run(user_input)
        except Exception as e:
            logger.error(f"Pi Coding Agent failed (streamed): {e}")
            raise RuntimeError(f"Pi Agent execution failed: {e}") from e

        inference_time = time.perf_counter() - inference_start
        logger.info(f"TIMING: [llm] Inference Latency (streamed): {inference_time:.4f}s")

        return response_text, self.display_provider, self.model

def get_llm_provider(provider_type: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    if not provider_type:
        provider_type = settings.DEFAULT_LLM_PROVIDER
    provider_type = provider_type.lower().strip()
    return PiFrameworkProvider(provider_type, model=model)

