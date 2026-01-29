# Third-Party Licenses

This document lists all third-party dependencies used by CodeConCat and their respective licenses.
All licenses were verified using external search tools (Exa AI) as of January 2026.

## Summary

CodeConCat uses dependencies under the following license types:
- **MIT License** - Most permissive, allows commercial use, modification, distribution
- **BSD-3-Clause License** - Similar to MIT, requires attribution
- **Apache-2.0 License** - Permissive, includes patent grant
- **MPL-2.0 License** - Weak copyleft, file-level
- **LGPL-2.1 License** - Weak copyleft, library linking permitted
- **PSF License** - Python Software Foundation License
- **ISC License** - Simplified BSD-style, very permissive

All licenses are compatible with CodeConCat's MIT license.

---

## Main Dependencies

| Package | Version Constraint | License | Description |
|---------|-------------------|---------|-------------|
| typer | ^0.16.1 | MIT | CLI framework with Rich support |
| rich | ^13.7.0 | MIT | Rich text and formatting in terminals |
| pydantic | ^2.0.0 | MIT | Data validation using Python type hints |
| annotated-types | >=0.4,<0.8 | MIT | Type annotation extensions |
| pydantic-settings | ^2.0.0 | MIT | Settings management for Pydantic |
| pyperclip | ^1.8.2 | BSD-3-Clause | Cross-platform clipboard module |
| tiktoken | ^0.11.0 | MIT | OpenAI's BPE tokenizer |
| fastapi | ^0.103.0 | MIT | Modern web framework for APIs |
| uvicorn | ^0.24.0 | BSD-3-Clause | ASGI server implementation |
| pathspec | ^0.11.0 | MPL-2.0 | Gitignore-style pattern matching |
| transformers | ^4.20.0 | Apache-2.0 | Hugging Face transformers library |
| semgrep | ^1.0.0 | LGPL-2.1 | Static analysis tool |
| httpx | ^0.25.0 | BSD-3-Clause | Async HTTP client |
| gitpython | ^3.1.30 | BSD-3-Clause | Git repository interaction |
| python-multipart | ^0.0.6 | Apache-2.0 | Streaming multipart parser |
| tree-sitter | >=0.20.7 | MIT | Incremental parsing system |
| tree-sitter-language-pack | ^0.7.2 | MIT | Language grammars for tree-sitter |
| tree-sitter-sql | ^0.3.10 | MIT | SQL grammar for tree-sitter |
| tree-sitter-hcl | ^1.2.0 | Apache-2.0 | HCL grammar for tree-sitter |
| jsonschema | ^4.20.0 | MIT | JSON Schema validation |
| cachetools | ^5.3.0 | MIT | Extensible memoizing collections |
| click-completion | ^0.5.2 | MIT | Shell completion for Click |
| python-dotenv | ^1.0.0 | BSD-3-Clause | .env file support |
| defusedxml | ^0.7.1 | PSF | Safe XML parsing (XXE prevention) |
| aiohttp | ^3.9.0 | Apache-2.0 | Async HTTP client/server |
| cryptography | ^41.0.0 | Apache-2.0 OR BSD-3-Clause | Cryptographic recipes and primitives |
| keyring | ^24.0.0 | MIT | System keyring access |
| pyyaml | ^6.0.0 | MIT | YAML parser and emitter |

## Development Dependencies

| Package | Version Constraint | License | Description |
|---------|-------------------|---------|-------------|
| ruff | ^0.1.0 | MIT | Fast Python linter |
| black | ^23.0.0 | MIT | Code formatter |
| isort | ^5.13.0 | MIT | Import sorter |
| mypy | ^1.7.0 | MIT | Static type checker |
| pre-commit | ^3.5.0 | MIT | Git hook framework |
| ipython | ^8.18.0 | BSD-3-Clause | Interactive Python shell |
| ipdb | ^0.13.13 | BSD-3-Clause | IPython debugger |
| types-pyyaml | ^6.0.12 | Apache-2.0 | Type stubs for PyYAML |

## Test Dependencies

| Package | Version Constraint | License | Description |
|---------|-------------------|---------|-------------|
| pytest | ^7.4.0 | MIT | Testing framework |
| pytest-cov | ^4.1.0 | MIT | Coverage plugin for pytest |
| pytest-asyncio | ^0.21.1 | Apache-2.0 | Async support for pytest |
| pytest-mock | ^3.11.1 | MIT | Mock support for pytest |
| pytest-timeout | ^2.2.0 | MIT | Timeout plugin for pytest |
| pytest-xdist | ^3.5.0 | MIT | Parallel test execution |
| hypothesis | ^6.92.0 | MPL-2.0 | Property-based testing |

## Documentation Dependencies

| Package | Version Constraint | License | Description |
|---------|-------------------|---------|-------------|
| mkdocs | ^1.5.3 | BSD-2-Clause | Documentation generator |
| mkdocs-material | ^9.5.0 | MIT | Material theme for MkDocs |
| mkdocstrings | ^0.24.0 | ISC | Auto-documentation from docstrings |
| mkdocs-typer | ^0.0.3 | MIT | Typer CLI documentation |

---

## License Texts

### MIT License

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### BSD-3-Clause License

```
BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### Apache-2.0 License

```
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### MPL-2.0 License

```
Mozilla Public License Version 2.0

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
```

### LGPL-2.1 License

```
GNU Lesser General Public License v2.1

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.
```

### PSF License (Python Software Foundation)

```
PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
Python Software Foundation; All Rights Reserved" are retained in Python alone or
in any derivative version prepared by Licensee.
```

### ISC License

```
ISC License

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

---

## License Compatibility Notes

1. **LGPL-2.1 (semgrep)**: CodeConCat uses semgrep as a library. LGPL allows linking
   to proprietary/MIT-licensed software. No source code disclosure required for
   CodeConCat since we don't modify semgrep's source.

2. **MPL-2.0 (pathspec, hypothesis)**: File-level copyleft. Changes to MPL-licensed
   files must be shared, but other files in the project are not affected.

3. **Apache-2.0**: Includes patent grants. Compatible with MIT license.

4. **Dual-licensed packages**: cryptography is dual-licensed under Apache-2.0 OR
   BSD-3-Clause, allowing choice of license.

---

*Last updated: January 2026*
*Developed by: Biostochastics*
