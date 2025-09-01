"""Tests for comprehensive attack pattern detection."""

from codeconcat.processor.attack_patterns import Severity, get_patterns_for_language, scan_content


class TestAttackPatterns:
    """Test attack pattern detection across languages."""

    def test_c_buffer_overflow_detection(self):
        """Test detection of buffer overflow vulnerabilities in C."""
        c_code = """
        void vulnerable_function(char *input) {
            char buffer[64];
            strcpy(buffer, input);  // Buffer overflow
            strcat(buffer, " suffix");  // Another overflow
            sprintf(buffer, "%s", input);  // Yet another
            gets(buffer);  // Dangerous function
        }
        """

        findings = scan_content(c_code, "c")
        assert len(findings) >= 4
        assert any(f["name"] == "buffer_overflow_strcpy" for f in findings)
        assert all(
            f["severity"] == Severity.CRITICAL.value
            for f in findings
            if f["name"] == "buffer_overflow_strcpy"
        )

    def test_python_code_injection(self):
        """Test detection of code injection in Python."""
        python_code = """
        def dangerous_function(user_input):
            # Code injection vulnerabilities
            eval(user_input)
            exec(user_input)
            result = eval(f"2 + {user_input}")

            # Command injection
            os.system("echo " + user_input)
            subprocess.Popen(f"ls {user_input}", shell=True)

            # SQL injection
            cursor.execute("SELECT * FROM users WHERE id = " + user_input)

            # Safe alternatives (should not trigger)
            eval("2 + 2")
            os.system("echo hello")
        """

        findings = scan_content(python_code, "python")

        # Check eval/exec injection
        eval_findings = [f for f in findings if "eval" in f["name"]]
        exec_findings = [f for f in findings if "exec" in f["name"]]
        assert len(eval_findings) >= 1
        assert len(exec_findings) >= 1

        # Check command injection
        cmd_findings = [f for f in findings if "command" in f["name"]]
        assert len(cmd_findings) >= 2

        # Check SQL injection
        sql_findings = [f for f in findings if "sql" in f["name"].lower()]
        assert len(sql_findings) >= 1

    def test_r_injection_patterns(self):
        """Test R-specific injection vulnerabilities."""
        r_code = """
        # Dangerous eval/parse pattern
        user_expr <- readline()
        result <- eval(parse(text = user_expr))

        # Command injection
        filename <- input$file
        system(paste("cat", filename))

        # SQL injection
        query <- paste("SELECT * FROM data WHERE id =", user_id)
        dbGetQuery(conn, query)

        # More direct SQL injection
        dbGetQuery(conn, paste("SELECT * FROM data WHERE id =", user_id))

        # Unsafe RDS loading
        data <- readRDS(input_file)
        """

        findings = scan_content(r_code, "r")

        assert any(f["name"] == "r_eval_parse_injection" for f in findings)
        assert any(f["name"] == "r_system_command_injection" for f in findings)
        assert any(f["name"] == "r_sql_injection" for f in findings)
        assert any(f["name"] == "r_unsafe_rds_load" for f in findings)

    def test_javascript_xss_detection(self):
        """Test XSS vulnerability detection in JavaScript."""
        js_code = """
        function updatePage(userInput) {
            // DOM XSS vulnerabilities
            document.getElementById('content').innerHTML = userInput;
            element.outerHTML = userInput;

            // React dangerouslySetInnerHTML
            return <div dangerouslySetInnerHTML={{__html: userInput}} />;

            // Eval injection
            eval(userInput);

            // Prototype pollution
            obj[userInput] = value;
            obj['__proto__'] = malicious;
            obj['constructor'] = evil;
        }
        """

        findings = scan_content(js_code, "javascript")

        # Check DOM XSS
        xss_findings = [f for f in findings if "xss" in f["name"].lower()]
        assert len(xss_findings) >= 3

        # Check prototype pollution
        proto_findings = [f for f in findings if "prototype" in f["name"]]
        assert len(proto_findings) >= 2

    def test_go_security_patterns(self):
        """Test Go security pattern detection."""
        go_code = """
        func vulnerableHandler(w http.ResponseWriter, r *http.Request) {
            // SQL injection
            userId := r.URL.Query().Get("id")
            db.Query("SELECT * FROM users WHERE id = " + userId)

            // Command injection
            filename := r.FormValue("file")
            exec.Command("cat", filename).Run()

            // Path traversal
            file := r.URL.Query().Get("file")
            data, _ := ioutil.ReadFile(file)

            // Weak random
            token := math/rand.Intn(1000000)
        }
        """

        findings = scan_content(go_code, "go")

        assert any(f["name"] == "go_sql_injection" for f in findings)
        assert any(f["name"] == "go_command_injection" for f in findings)
        assert any(f["name"] == "go_path_traversal" for f in findings)
        assert any(f["name"] == "go_weak_random" for f in findings)

    def test_php_vulnerabilities(self):
        """Test PHP vulnerability detection."""
        php_code = """
        <?php
        // SQL injection
        $id = $_GET['id'];
        mysql_query("SELECT * FROM users WHERE id = " . $id);

        // Command injection
        system($_POST['cmd']);
        exec("ls " . $_REQUEST['dir']);

        // File inclusion
        include($_GET['page'] . '.php');

        // Unserialize vulnerability
        $data = unserialize($_COOKIE['data']);

        // XSS
        echo "Welcome " . $_GET['name'];
        ?>
        """

        findings = scan_content(php_code, "php")

        assert any(f["name"] == "php_sql_injection" for f in findings)
        assert any(f["name"] == "php_command_injection" for f in findings)
        assert any(f["name"] == "php_file_inclusion" for f in findings)
        assert any(f["name"] == "php_unserialize" for f in findings)
        assert any(f["name"] == "php_xss" for f in findings)

    def test_rust_safety_issues(self):
        """Test Rust safety issue detection."""
        rust_code = """
        fn dangerous_function() {
            // Unwrap without error handling
            let value = some_result.unwrap();
            let data = file.read().expect("Failed to read");

            // Unsafe transmute
            let bytes: [u8; 4] = unsafe { mem::transmute(42u32) };

            // Raw pointers
            let ptr: *mut i32 = &mut value as *mut i32;

            // Mutable static
            static mut COUNTER: i32 = 0;
        }
        """

        findings = scan_content(rust_code, "rust")

        assert any(f["name"] == "rust_unsafe_unwrap" for f in findings)
        assert any(f["name"] == "rust_unsafe_transmute" for f in findings)
        assert any(f["name"] == "rust_unsafe_raw_pointer" for f in findings)
        assert any(f["name"] == "rust_static_mut" for f in findings)

    def test_julia_patterns(self):
        """Test Julia security patterns."""
        julia_code = """
        # Eval injection
        user_code = readline()
        result = eval(Meta.parse(user_code))

        # Command injection
        filename = get_user_input()
        run(`cat $filename`)

        # Unsafe ccall
        lib_name = user_input
        ccall((func_name, lib_name), Cvoid, ())

        # Including untrusted code
        include(user_file)
        """

        findings = scan_content(julia_code, "julia")

        assert any(f["name"] == "julia_eval_injection" for f in findings)
        assert any(f["name"] == "julia_command_injection" for f in findings)
        assert any(f["name"] == "julia_unsafe_ccall" for f in findings)
        assert any(f["name"] == "julia_include_injection" for f in findings)

    def test_cross_language_patterns(self):
        """Test patterns that apply across languages."""
        code_with_secrets = """
        # Hardcoded secrets
        api_key = "sk_test_abcdef123456789"
        secret_key = "supersecretpassword123"
        private_key = "-----BEGIN RSA PRIVATE KEY-----"

        # Base64 obfuscation
        encoded = "SGVsbG8gV29ybGQhIFRoaXMgaXMgYSBsb25nIGJhc2U2NCBlbmNvZGVkIHN0cmluZyB0aGF0IG1pZ2h0IGJlIHN1c3BpY2lvdXM="

        # Cryptocurrency wallets
        btc_wallet = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        eth_wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f7e8E7"
        """

        # Test with Python
        findings = scan_content(code_with_secrets, "python")

        secret_findings = [f for f in findings if "secret" in f["name"] or "hardcoded" in f["name"]]
        assert len(secret_findings) >= 2

        crypto_findings = [f for f in findings if "cryptocurrency" in f["name"]]
        assert len(crypto_findings) >= 2

        base64_findings = [f for f in findings if "base64" in f["name"]]
        assert len(base64_findings) >= 1

    def test_language_pattern_mapping(self):
        """Test that language pattern mapping works correctly."""
        # Test known languages
        c_patterns = get_patterns_for_language("c")
        assert any(p.name == "buffer_overflow_strcpy" for p in c_patterns)

        python_patterns = get_patterns_for_language("python")
        assert any(p.name == "python_eval_injection" for p in python_patterns)

        # Test case insensitivity
        python_patterns_upper = get_patterns_for_language("PYTHON")
        assert len(python_patterns) == len(python_patterns_upper)

        # Test unknown language gets cross-language patterns only
        unknown_patterns = get_patterns_for_language("unknown_lang")
        assert all(p.languages == ["all"] for p in unknown_patterns)

    def test_severity_levels(self):
        """Test that severity levels are correctly assigned."""
        # Critical severity patterns
        critical_code = """
        eval(user_input)
        os.system(user_command)
        """
        findings = scan_content(critical_code, "python")
        critical_findings = [f for f in findings if f["severity"] == Severity.CRITICAL.value]
        assert len(critical_findings) >= 2

        # Medium severity patterns
        medium_code = """
        import hashlib
        password_hash = hashlib.md5(password)
        """
        findings = scan_content(medium_code, "python")
        medium_findings = [f for f in findings if f["severity"] == Severity.MEDIUM.value]
        assert len(medium_findings) >= 1

    def test_line_number_calculation(self):
        """Test that line numbers are correctly calculated."""
        multiline_code = """line 1
line 2
eval(user_input)  # Should be line 3
line 4
exec(another_input)  # Should be line 5
"""

        findings = scan_content(multiline_code, "python")
        eval_finding = next(f for f in findings if "eval" in f["name"])
        exec_finding = next(f for f in findings if "exec" in f["name"])

        assert eval_finding["line"] == 3
        assert exec_finding["line"] == 5

    def test_cwe_ids(self):
        """Test that CWE IDs are properly assigned."""
        sql_injection_code = "cursor.execute('SELECT * FROM users WHERE id = ' + user_id)"
        findings = scan_content(sql_injection_code, "python")

        sql_findings = [f for f in findings if "sql" in f["name"]]
        assert len(sql_findings) > 0
        assert sql_findings[0]["cwe_id"] == "CWE-89"  # SQL Injection CWE
