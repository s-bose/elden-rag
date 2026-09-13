from pydantic import BaseModel

from app.constants import ScraperCategory


class CategoryConfig(BaseModel):
    seeds: list[str]
    recursive: bool = False
    max_depth: int = 0
    allow_patterns: list[str] | None = None


CATEGORIES: dict[ScraperCategory, CategoryConfig] = {
    ScraperCategory.weapons: CategoryConfig(
        seeds=["/Weapons"],
        recursive=True,
        max_depth=1,
        allow_patterns=[
            "how to get",
            "where to find",
            "stats",
            "requirements",
            "skill",
            "moveset",
            "scaling",
            "upgrade",
            "notes",
            "lore",
        ],
    ),
    ScraperCategory.armor: CategoryConfig(
        seeds=["/Armor"],
        allow_patterns=["how to get", "where to find", "stats", "effects", "notes", "lore"],
    ),
    ScraperCategory.talismans: CategoryConfig(
        seeds=["/Talismans"],
        allow_patterns=["how to get", "where to find", "effect", "notes", "lore"],
    ),
    ScraperCategory.ashes_of_war: CategoryConfig(
        seeds=["/Ashes+of+War"],
        allow_patterns=["how to get", "where to find", "effect", "skill", "affinity", "notes"],
    ),
    ScraperCategory.items_consumables: CategoryConfig(
        seeds=["/Items", "/Consumables", "/Key+Items", "/Crafting+Materials"],
        allow_patterns=["how to get", "where to find", "effect", "use", "notes", "lore"],
    ),
    ScraperCategory.bosses: CategoryConfig(
        seeds=["/Bosses"],
        allow_patterns=[
            "where to find",
            "combat information",
            "negations",
            "resistances",
            "lore",
        ],
    ),
    ScraperCategory.npcs: CategoryConfig(
        seeds=["/NPCs"],
        allow_patterns=["location", "where to find", "quest", "dialogue", "notes", "lore"],
    ),
    ScraperCategory.locations: CategoryConfig(
        seeds=["/Locations"],
        allow_patterns=[
            "description",
            "enemies",
            "items",
            "npcs",
            "bosses",
            "how to get",
            "notes",
        ],
    ),
    ScraperCategory.walkthrough: CategoryConfig(
        seeds=["/Walkthrough"],
        recursive=True,
        max_depth=2,
        allow_patterns=None,
    ),
    ScraperCategory.side_quests: CategoryConfig(
        seeds=["/Side+Quests"],
        recursive=True,
        max_depth=1,
        allow_patterns=None,
    ),
}
