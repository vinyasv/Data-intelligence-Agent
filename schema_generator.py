"""
Schema Generator Module

Generates Pydantic schemas dynamically from natural language queries using Claude 4.5.
"""
import re
import json
from typing import Tuple, Type, Any
from pydantic import BaseModel
from anthropic import Anthropic

from config import settings
from models import SchemaGenerationResult, SchemaGenerationError
from utils import logger


SCHEMA_GENERATION_PROMPT = """You are a Pydantic schema generation expert. Your task is to generate a valid Pydantic v2 model based on the user's natural language extraction query.

**IMPORTANT RULES:**
1. Generate ONLY valid Python code for a Pydantic v2 model
2. Use proper type hints: str, int, float, bool, Optional[T], List[T]
3. For lists of items, create a container model with a list field
4. Use Optional[] for fields that might not exist
5. Add Field(..., description="...") for clarity when helpful
6. Do NOT include any explanations, markdown formatting, or text outside the code
7. The code must be executable as-is
8. Always create at least two models: an item model and a container model

**EXAMPLE 1:**
Query: "Extract job listings with title, company, salary range, and remote status"

Output:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class JobListing(BaseModel):
    title: str
    company: str
    salary_range: Optional[str] = None
    is_remote: bool
    location: Optional[str] = None

class JobListings(BaseModel):
    jobs: List[JobListing] = Field(default_factory=list, description="List of job listings")
```

**EXAMPLE 2:**
Query: "Get product name, price, rating, and stock status"

Output:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class Product(BaseModel):
    name: str
    price: str
    rating: Optional[float] = None
    in_stock: bool

class ProductList(BaseModel):
    products: List[Product] = Field(default_factory=list, description="List of products")
```

**EXAMPLE 3:**
Query: "Extract articles with headline, author, date, and a one-sentence summary"

Output:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class Article(BaseModel):
    headline: str
    author: Optional[str] = None
    publish_date: str
    summary: str = Field(description="One-sentence summary of the article")

class ArticleList(BaseModel):
    articles: List[Article] = Field(default_factory=list, description="List of articles")
```

Now generate a Pydantic model for this query:
{query}

Remember: Output ONLY the Python code, no explanations or markdown."""


class SchemaGenerator:
    """
    Generates Pydantic schemas from natural language queries using Claude.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize schema generator with Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    async def generate_schema(self, query: str) -> SchemaGenerationResult:
        """
        Generate Pydantic schema from natural language query.

        Args:
            query: Natural language extraction query

        Returns:
            SchemaGenerationResult with model code, class name, and JSON schema

        Raises:
            SchemaGenerationError: If schema generation fails
        """
        try:
            logger.info(f"Generating schema for query: {query[:100]}...")

            # Call Claude to generate schema
            response = self.client.messages.create(
                model=self.model,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": SCHEMA_GENERATION_PROMPT.format(query=query)
                    }
                ]
            )

            # Extract generated code
            raw_response = response.content[0].text
            pydantic_code = self._extract_code(raw_response)

            # Validate and compile the model
            model_name, compiled_model = self._compile_model(pydantic_code)

            # Generate JSON schema
            json_schema = compiled_model.model_json_schema()

            logger.info(f"Successfully generated schema: {model_name}")

            return SchemaGenerationResult(
                query=query,
                pydantic_code=pydantic_code,
                json_schema=json_schema,
                model_name=model_name
            )

        except Exception as e:
            logger.error(f"Schema generation failed: {str(e)}")
            raise SchemaGenerationError(f"Failed to generate schema: {str(e)}")

    def _extract_code(self, raw_response: str) -> str:
        """
        Extract Python code from Claude's response.

        Args:
            raw_response: Raw response from Claude

        Returns:
            Cleaned Python code

        Raises:
            SchemaGenerationError: If code cannot be extracted
        """
        # Try to extract code from markdown blocks
        code_block_match = re.search(r'```python\n(.*?)```', raw_response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try without language specifier
        code_block_match = re.search(r'```\n(.*?)```', raw_response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # If no code blocks, assume entire response is code
        if 'class' in raw_response and 'BaseModel' in raw_response:
            return raw_response.strip()

        raise SchemaGenerationError("Could not extract valid Python code from response")

    def _compile_model(self, pydantic_code: str) -> Tuple[str, Type[BaseModel]]:
        """
        Compile and validate Pydantic model code.

        Args:
            pydantic_code: Python code defining Pydantic models

        Returns:
            Tuple of (model_name, compiled_model_class)

        Raises:
            SchemaGenerationError: If compilation fails
        """
        try:
            # Create execution namespace
            namespace = {
                'BaseModel': BaseModel,
                'Field': __import__('pydantic').Field,
                'Optional': __import__('typing').Optional,
                'List': __import__('typing').List,
                'Literal': __import__('typing').Literal,
            }

            # Execute code to define models
            exec(pydantic_code, namespace)

            # Find the container model (last defined class or one with List field)
            model_classes = [
                (name, obj) for name, obj in namespace.items()
                if isinstance(obj, type) and issubclass(obj, BaseModel) and obj != BaseModel
            ]

            if not model_classes:
                raise SchemaGenerationError("No Pydantic models found in generated code")

            # Prefer the last defined model (typically the container)
            model_name, model_class = model_classes[-1]

            # Validate it's a proper Pydantic model
            _ = model_class.model_json_schema()

            logger.debug(f"Compiled model: {model_name}")
            return model_name, model_class

        except Exception as e:
            logger.error(f"Model compilation failed: {str(e)}")
            raise SchemaGenerationError(f"Failed to compile Pydantic model: {str(e)}")

    def get_model_class(self, pydantic_code: str) -> Type[BaseModel]:
        """
        Get compiled model class from code (for reuse in extraction).

        Args:
            pydantic_code: Python code defining Pydantic models

        Returns:
            Compiled Pydantic model class
        """
        _, model_class = self._compile_model(pydantic_code)
        return model_class


# Convenience function for direct usage
async def generate_schema(query: str) -> SchemaGenerationResult:
    """
    Generate Pydantic schema from natural language query.

    Args:
        query: Natural language extraction query

    Returns:
        SchemaGenerationResult with model code and JSON schema
    """
    generator = SchemaGenerator()
    return await generator.generate_schema(query)
