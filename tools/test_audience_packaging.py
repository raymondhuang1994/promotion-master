"""Check real self-contained distributions, not generated prose or audience semantics.

Run after audience-editions.md and its three entrypoints/manifests have been synced.
The existing packager writes only to a fresh TemporaryDirectory, never repo dist/.
Private-path checks are not a substitute for reviewing text before publication.
"""
import importlib.util
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import unittest
import warnings
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("promotion-master", "product-slogan", "sales-qa-battlecard")
GUIDE = "references/audience-editions.md"
RESOURCE_PATH = re.compile(
    r"(?<![\w./])(?:references|assets|scripts|examples)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+"
)
FORBIDDEN_PARTS = {
    "node_modules", "__pycache__", ".ds_store", ".git", ".env",
    "private", ".private", "docs", "evals", "gold", "replay-log.md", "work", ".venv",
}


def manifest_entries(text):
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


class AudiencePackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "audience_test_packager", ROOT / "tools/package_skills.py"
        )
        packager = importlib.util.module_from_spec(spec)
        # Importing the real tool must not create __pycache__ in the checkout.
        with patch.object(sys, "dont_write_bytecode", True):
            spec.loader.exec_module(packager)
        cls.tmp = tempfile.TemporaryDirectory(prefix="audience-packaging-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.output = Path(cls.tmp.name)
        cls.archives = {}
        cls.prompts = {}
        with patch.object(packager, "DIST", str(cls.output)), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            for skill in SKILLS:
                errors = packager.check(skill)
                if errors:
                    raise AssertionError(f"{skill}: {errors}")
                cls.archives[skill] = Path(packager.zip_skill(skill))
                cls.prompts[skill] = Path(packager.prompt_pack(skill))
        cls.resource_warnings = [str(item.message) for item in caught
                                 if issubclass(item.category, ResourceWarning)]

    def test_packaging_closes_its_file_handles(self):
        self.assertEqual(self.resource_warnings, [])

    def test_three_packages_ship_the_current_declared_guide(self):
        shared = ROOT / "shared" / GUIDE
        self.assertTrue(shared.is_file(), f"Missing source guide: {shared}")
        expected = shared.read_bytes()
        self.assertTrue(expected.strip(), "The audience guide must not be empty")
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                entries = manifest_entries(archive.read(f"{skill}/shared.txt").decode("utf-8"))
                self.assertIn(GUIDE, entries, f"{skill} must declare its own copy")
                self.assertEqual(archive.read(f"{skill}/{GUIDE}"), expected)
                self.assertEqual((ROOT / "skills" / skill / GUIDE).read_bytes(), expected)
                self.assertIn(expected.decode("utf-8"), self.prompts[skill].read_text(encoding="utf-8"))

    def test_entrypoint_resource_paths_resolve_inside_each_real_archive(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                names = set(archive.namelist())
                entrypoint = archive.read(f"{skill}/SKILL.md").decode("utf-8")
                references = set(RESOURCE_PATH.findall(entrypoint))
                self.assertIn(GUIDE, references, f"{skill} must link the guide locally")
                guide = archive.read(f"{skill}/{GUIDE}").decode("utf-8")
                references.update(RESOURCE_PATH.findall(guide))
                for relative in sorted(references):
                    self.assertIn(f"{skill}/{relative}", names,
                                  f"{skill}: unresolved packaged resource {relative}")

    def test_manifest_files_exist_and_match_the_shared_sources(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                entries = manifest_entries(archive.read(f"{skill}/shared.txt").decode("utf-8"))
                for relative in entries:
                    path = PurePosixPath(relative)
                    self.assertFalse(path.is_absolute(), relative)
                    self.assertNotIn("..", path.parts, relative)
                    self.assertEqual(archive.read(f"{skill}/{relative}"),
                                     (ROOT / "shared" / relative).read_bytes(),
                                     f"{skill}: stale shared resource {relative}")

    def test_reference_guides_resolve_their_sibling_markdown_links(self):
        # Entry-point checks alone miss a required guide linking another guide.
        sibling_link = re.compile(r"`([A-Za-z0-9_-]+\.md)`")
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                names = set(archive.namelist())
                directory = f"{skill}/references/"
                for name in sorted(names):
                    if name.startswith(directory) and name.endswith(".md"):
                        content = archive.read(name).decode("utf-8")
                        for target in sibling_link.findall(content):
                            self.assertIn(directory + target, names,
                                          f"{name}: unresolved sibling guide {target}")

    def test_distributions_exclude_dependency_private_and_external_paths(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                self.assertEqual(self.archives[skill].parent, self.output)
                self.assertEqual(self.prompts[skill].parent, self.output / "prompts")
                base = (ROOT / "skills" / skill).resolve()
                for name in archive.namelist():
                    path = PurePosixPath(name)
                    self.assertFalse(path.is_absolute(), name)
                    self.assertNotIn("..", path.parts, name)
                    self.assertEqual(path.parts[0], skill, name)
                    self.assertNotIn(path.suffix.lower(), {".docx", ".pdf", ".pptx", ".xlsx"}, name)
                    for part in path.parts:
                        self.assertNotIn(part.lower(), FORBIDDEN_PARTS, name)
                        self.assertFalse(part.lower().startswith(".env."), name)
                    source = base.joinpath(*path.parts[1:])
                    try:
                        source.resolve().relative_to(base)
                    except ValueError:
                        self.fail(f"Archive included a source outside its skill: {name}")

    def test_real_packages_include_license_and_current_host_metadata(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), zipfile.ZipFile(self.archives[skill]) as archive:
                for relative in ("LICENSE", "agents/openai.yaml"):
                    expected = (ROOT / "skills" / skill / relative).read_bytes()
                    self.assertTrue(expected.strip(), relative)
                    self.assertEqual(archive.read(f"{skill}/{relative}"), expected)

    def test_prompt_pack_recursively_preserves_real_workspace_templates(self):
        skill = "promotion-master"
        prompt = self.prompts[skill].read_text(encoding="utf-8")
        templates = list((ROOT / "skills" / skill / "assets/workspace").rglob("*.md"))
        self.assertGreater(len(templates), 1)
        for source in templates:
            relative = source.relative_to(ROOT / "skills" / skill).as_posix()
            with self.subTest(template=relative):
                self.assertIn(f"<!-- {relative} -->", prompt)
                self.assertIn(source.read_text(encoding="utf-8"), prompt)


if __name__ == "__main__":
    unittest.main()
