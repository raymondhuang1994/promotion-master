"""Exercise actual release files and isolated copies of real skills.

No generated skill prose substitutes for repository content. Negative cases add
files only to temporary copies, and all distribution output stays in temp dirs.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("release_test_packager", ROOT / "tools/package_skills.py")
        cls.packager = importlib.util.module_from_spec(spec)
        with patch.object(sys, "dont_write_bytecode", True):
            spec.loader.exec_module(cls.packager)
        cls.tmp = tempfile.TemporaryDirectory(prefix="release-packaging-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.output = Path(cls.tmp.name) / "dist"
        cls.skills = sorted(path.name for path in (ROOT / "skills").iterdir() if (path / "SKILL.md").is_file())
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools/package_skills.py"), "--prompt-pack",
             "--output-dir", str(cls.output)], capture_output=True, text=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_flat_release_checksums_match_every_downloadable_file(self):
        release = self.output / "release"
        expected = {f"{skill}{suffix}" for skill in self.skills for suffix in (".skill", ".zip", "-prompt.md")}
        actual = {path.name for path in release.iterdir() if path.name != "SHA256SUMS"}
        self.assertEqual(actual, expected)
        checksums = {}
        for line in (release / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(Path(name).name, name, "Release downloads must verify without directory reconstruction")
            self.assertNotIn(name, checksums)
            checksums[name] = digest
            self.assertEqual(digest, hashlib.sha256((release / name).read_bytes()).hexdigest(), name)
        self.assertEqual(set(checksums), actual)
        self.assertNotIn("SHA256SUMS", checksums)
        checker = shutil.which("sha256sum") or shutil.which("shasum")
        if checker:
            args = [checker] + (["-a", "256"] if Path(checker).name == "shasum" else [])
            result = subprocess.run(args + ["-c", "SHA256SUMS"], cwd=release, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # The developer distribution also covers every generated nested artifact.
        root_checksums = dict(line.split("  ", 1)[::-1]
                              for line in (self.output / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
        root_files = {path.relative_to(self.output).as_posix() for path in self.output.rglob("*")
                      if path.is_file() and path != self.output / "SHA256SUMS"}
        self.assertEqual(set(root_checksums), root_files)
        for name, digest in root_checksums.items():
            self.assertEqual(digest, hashlib.sha256((self.output / name).read_bytes()).hexdigest(), name)

    def test_real_archives_and_flat_release_copies_are_byte_identical(self):
        for skill in self.skills:
            with self.subTest(skill=skill):
                original = (self.output / f"{skill}.skill").read_bytes()
                for candidate in (self.output / f"{skill}.zip", self.output / "release" / f"{skill}.skill",
                                  self.output / "release" / f"{skill}.zip"):
                    self.assertEqual(candidate.read_bytes(), original)
                with zipfile.ZipFile(self.output / f"{skill}.skill") as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                    for resource in ("LICENSE", "agents/openai.yaml", "SKILL.md", "shared.txt"):
                        self.assertEqual(archive.read(f"{skill}/{resource}"),
                                         (ROOT / "skills" / skill / resource).read_bytes())

    def test_text_only_boundary_precedes_instructions_and_nested_templates_survive(self):
        for skill in self.skills:
            with self.subTest(skill=skill):
                prompt = (self.output / "prompts" / f"{skill}.md").read_text(encoding="utf-8")
                self.assertEqual(prompt, (self.output / "release" / f"{skill}-prompt.md").read_text(encoding="utf-8"))
                prefix = "\n".join(prompt.splitlines()[:5])
                self.assertIn("纯文本", prefix)
                self.assertIn("不含可执行脚本", prefix)
                self.assertIn("完整 .skill 或 .zip 技能目录", prefix)
                self.assertIn((ROOT / "skills" / skill / "LICENSE").read_text(encoding="utf-8"), prompt)
                for directory in ("references", "assets"):
                    for source in (ROOT / "skills" / skill / directory).rglob("*.md"):
                        relative = source.relative_to(ROOT / "skills" / skill).as_posix()
                        self.assertIn(f"<!-- {relative} -->", prompt)
                        self.assertIn(source.read_text(encoding="utf-8"), prompt, relative)
                self.assertNotIn("<!-- scripts/", prompt)

    def test_archives_are_deterministic_after_source_timestamps_change(self):
        skill = "product-slogan"
        with tempfile.TemporaryDirectory(prefix="release-determinism-") as temp:
            skills = Path(temp) / "skills"
            copy = skills / skill
            shutil.copytree(ROOT / "skills" / skill, copy)
            with patch.object(self.packager, "SKILLS", str(skills)), patch.object(self.packager, "DIST", str(Path(temp) / "dist")):
                first = Path(self.packager.zip_skill(skill)).read_bytes()
                for source in copy.rglob("*"):
                    if source.is_file():
                        os.utime(source, (1_000_000_000, 1_000_000_000))
                second = Path(self.packager.zip_skill(skill)).read_bytes()
                self.assertEqual(first, second)

    def test_forbidden_files_are_excluded_from_real_skill_copies(self):
        skill = "product-slogan"
        forbidden = ("docs/client.md", "private/client.md", "assets/private/client.md", "assets/client.docx",
                     "assets/client.pdf", "scripts/node_modules/dependency/index.js", "scripts/.env", "scripts/.env.local")
        with tempfile.TemporaryDirectory(prefix="release-exclusions-") as temp:
            skills = Path(temp) / "skills"
            copy = skills / skill
            shutil.copytree(ROOT / "skills" / skill, copy)
            for relative in forbidden:
                source = copy / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("Forbidden packaging test fixture", encoding="utf-8")
            with patch.object(self.packager, "SKILLS", str(skills)), patch.object(self.packager, "DIST", str(Path(temp) / "dist")):
                with zipfile.ZipFile(self.packager.zip_skill(skill)) as archive:
                    names = set(archive.namelist())
                    for relative in forbidden:
                        self.assertNotIn(f"{skill}/{relative}", names)
                self.assertNotIn("Forbidden packaging test fixture", Path(self.packager.prompt_pack(skill)).read_text(encoding="utf-8"))

    def test_missing_release_resources_local_paths_and_symlinks_stop_packaging(self):
        skill = "product-slogan"
        for problem in ("LICENSE", "agents/openai.yaml", "missing-template", "local-path", "local-directory", "windows-path", "symlink"):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory(prefix="release-reject-") as temp:
                skills = Path(temp) / "skills"
                copy = skills / skill
                shutil.copytree(ROOT / "skills" / skill, copy)
                if problem in ("LICENSE", "agents/openai.yaml"):
                    (copy / problem).unlink()
                elif problem == "missing-template":
                    (copy / "assets/one-pager-template.md").unlink()
                elif problem == "local-path":
                    (copy / "references/local-path.md").write_text("/Users/release-fixture/private/source.docx", encoding="utf-8")
                elif problem == "local-directory":
                    (copy / "references/local-path.md").write_text("/home/release-fixture", encoding="utf-8")
                elif problem == "windows-path":
                    (copy / "references/local-path.md").write_text(r"C:\Users\release-fixture\private\source.docx", encoding="utf-8")
                else:
                    (copy / "references/external.md").symlink_to(ROOT / "README.md")
                output = Path(temp) / "dist"
                with patch.object(self.packager, "SKILLS", str(skills)), patch.object(self.packager, "DIST", str(output)):
                    self.assertTrue(self.packager.check(skill))
                    with self.assertRaises(ValueError):
                        self.packager.zip_skill(skill)
                    self.assertFalse(output.exists())

    def test_checksum_creation_refuses_untracked_files_without_deleting_them(self):
        with tempfile.TemporaryDirectory(prefix="release-stale-") as temp:
            output = Path(temp)
            source = self.output / "promotion-master.skill"
            artifact = output / source.name
            shutil.copyfile(source, artifact)
            stale = output / "unrelated.txt"
            stale.write_text("User-owned file", encoding="utf-8")
            with patch.object(self.packager, "DIST", str(output)):
                with self.assertRaises(ValueError):
                    self.packager.write_checksums([artifact])
            self.assertEqual(stale.read_text(encoding="utf-8"), "User-owned file")
            self.assertFalse((output / "SHA256SUMS").exists())


if __name__ == "__main__":
    unittest.main()
