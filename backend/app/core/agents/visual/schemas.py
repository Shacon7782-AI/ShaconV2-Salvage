from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class VisualAssetRequest(BaseModel):
    """Input: What the wireframe needs"""
    element_id: str = Field(..., description="ID from wireframe, e.g., 'hero_bg_01'")
    context_description: str = Field(..., description="e.g., 'Background for a banking app hero section'")
    dimensions: str = Field(..., description="Aspect ratio or pixel size, e.g., '1920x1080'")

class BrandStyleContext(BaseModel):
    """Input: The brand identity"""
    mood_keywords: List[str] = Field(..., description="e.g., ['trustworthy', 'corporate', 'blue']")
    color_palette: List[str] = Field(..., description="Hex codes")
    visual_reference: str = Field(..., description="Style embedding or reference URL")

class ImageGenerationPrompt(BaseModel):
    """Output: The instruction for the Image Model"""
    element_id: str
    positive_prompt: str = Field(..., description="Detailed prompt for DALL-E/SDXL")
    negative_prompt: str = Field(..., description="What to avoid (e.g., 'text, blur')")
    model_parameters: Dict[str, Any] = Field(..., description="Size, style presets, etc.")

class IconSelection(BaseModel):
    """Output: Selected Icon from a library"""
    element_id: str = Field(..., description="ID from wireframe/component where icon is needed")
    icon_name: str = Field(..., description="Name of the icon in lucide-react (e.g., 'Zap')")
    library: str = Field("lucide-react", description="Icon library source")

class VisualDesignAgentOutput(BaseModel):
    assets_to_generate: List[ImageGenerationPrompt]
    selected_icons: List[IconSelection] = []
