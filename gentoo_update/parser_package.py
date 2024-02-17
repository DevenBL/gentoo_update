"""Classes and methods for parsing log files.

Specifically logfiles generated by Gentoo Linux's emerge package manager.
"""

import re
from typing import List

from .report_objects import PackageInfo


class PackageParser:
    """A class that provides methods to parse package specific information."""

    def __init__(self) -> None:
        """Initialize PackageParser class."""
        pass

    def _parse_package_string(self, package_string: str) -> List[str]:
        """Parse package string into multiple parts.

        Args:
        ----
            package_string (str): String containing package information.

        Returns:
        -------
            List: List containing package information parts.
        """
        split_package_string = []
        temp = ""
        quotes_count = 0
        brackets_count = 0

        for char in package_string:
            temp += char
            if char == '"':
                quotes_count += 1
            elif char == "[":
                brackets_count += 1
            elif char == "]":
                brackets_count -= 1

            if char == " " and quotes_count % 2 == 0 and brackets_count == 0:
                split_package_string.append(temp.strip())
                temp = ""

        if temp:
            split_package_string.append(temp.strip())

        return split_package_string

    def _determine_update_status(self, update_status: str) -> str:
        """Determine what happens to the package during update.

        Args:
        ----
            update_status: String with following format - [ebuild  rR    ]

        Returns:
        -------
            status: Simplified package status.
        """
        status = ""
        match update_status:
            case str(x) if "N" in x:
                status += "NewPackage"
            case str(x) if "R" in x:
                status += "ReEmerge"
            case str(x) if "U" in x:
                status += "Update"
            case _:
                status += "Undefined"

        return status

    def _parse_package_ebuild(self, split_package_string: List) -> PackageInfo:
        """Parse ebuild information.

        Args:
        ----
            split_package_string (List[str]): A list with ebuild info, example:
                ['[ebuild     U  ]', 'sys-devel/gnuconfig-20230731::gentoo',
                 '[20230121::gentoo]', '72', 'KiB']

        Returns:
        -------
            PackageInfo: PackageInfo object with processed information
        """
        package_type = "ebuild"
        update_status = self._determine_update_status(split_package_string[0])
        package_base_info = split_package_string[1]
        repo = package_base_info.split("::")[1]
        name_newversion = package_base_info.split("::")[0]

        package_name = ""
        for part in name_newversion.split("-"):
            if part.isnumeric() is True:
                pass
            elif "." in part or ":" in part:
                pass
            elif len(part) == 2 and part[0] == "r" and part[1].isnumeric():
                pass
            else:
                package_name += f"{part}-"

        new_version = name_newversion.replace(package_name, "")
        old_version = split_package_string[2].split("::")[0][1:]
        package_name = package_name[:-1]

        ebuild_info = PackageInfo(
            package_type,
            package_name,
            new_version,
            old_version,
            update_status,
            repo,
        )

        for var in split_package_string:
            if '="' in var:
                splitvar = var.split("=")
                ebuild_info.add_attributes({splitvar[0]: splitvar[1][1:-1].split(" ")})

        return ebuild_info

    def _parse_package_blocks(self, split_package_string: List[str]) -> PackageInfo:
        """Parse blocks information.

        Args:
        ----
            split_package_string (List[str]): A list with blocks info, example:
                ['[blocks b      ]', '<perl-core/Compress-Raw-Zlib-2.204.1_rc',
                 '("<perl-core/Compress-Raw-Zlib-2.204.1_rc"', 'is', 'soft',
                 'blocking', 'virtual/perl-Compress-Raw-Zlib-2.204.1_rc)']

        Returns:
        -------
            PackageInfo: PackageInfo object with processed information
        """
        package_type = "blocks"
        package_name = split_package_string[1][1:]
        new_version = None
        old_version = None
        update_status = split_package_string[0]
        repo = None

        blocks_info = PackageInfo(
            package_type,
            package_name,
            new_version,
            old_version,
            update_status,
            repo,
        )

        blocks_info.add_attributes({"blocked_package": split_package_string[-1][:-1]})
        return blocks_info

    def _parse_package_uninstall(self, split_package_string: List[str]) -> PackageInfo:
        """Parse uninstall information.

        Args:
        ----
            split_package_string (List[str]): A list with uninstall info

        Example:
        -------
            ['[uninstall     ]', 'perl-core/Compress-Raw-Zlib-2.202.0::gentoo']

        Returns:
        -------
            PackageInfo: PackageInfo object with processed information
        """
        package_type = "uninstall"
        split_package_info = split_package_string[1].split("::")
        package_name = split_package_info[0]
        repo = split_package_info[1]
        new_version = None
        old_version = None
        update_status = split_package_string[0]

        uninstall_info = PackageInfo(
            package_type,
            package_name,
            new_version,
            old_version,
            update_status,
            repo,
        )

        uninstall_info.add_attributes({"uninstalled_package": package_name})
        return uninstall_info

    def parse_update_details(self, section_content: List[str]) -> List[PackageInfo]:
        """Parse information about update from log file.

        Args:
        ----
            section_content (List[str]): A list where each item is
                one line of logs from a section.

        Returns:
        -------
            List[PackageInfo]: List of PackageInfo objects where each object
                contains useful information for the report.
        """
        ebuild_info_pattern = r"\[(.+?)\]"
        package_strings = [
            line
            for line in section_content
            if re.search(ebuild_info_pattern, line) and line != "[ ok ]"
        ]
        packages = []
        for package_string in package_strings:
            split_package_string = self._parse_package_string(package_string)
            update_status = split_package_string[0]

            package = None
            if "ebuild" in update_status:
                package = self._parse_package_ebuild(split_package_string)
            elif "blocks" in update_status:
                package = self._parse_package_blocks(split_package_string)
            elif "uninstall" in update_status:
                package = self._parse_package_uninstall(split_package_string)

            if package:
                packages.append(package)

        return packages
