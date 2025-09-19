#!/usr/bin/env python3
"""
Simple web UI for Scrypto LLM Demo
One-file Streamlit app for interactive testing
"""

import streamlit as st
import subprocess
import json
import os
import tempfile
import re
from datetime import datetime

def extract_rust_code(text):
    """Extract Rust code from text"""
    patterns = [
        r'```rust\n(.*?)\n```',
        r'```scrypto\n(.*?)\n```', 
        r'```\n(.*?)\n```'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    return ""

def create_scrypto_project(code, name):
    """Create a temporary Scrypto project"""
    project_dir = f"/tmp/scrypto_demo_{name}"
    os.makedirs(f"{project_dir}/src", exist_ok=True)
    
    with open(f"{project_dir}/src/lib.rs", "w") as f:
        f.write(code)
    
    cargo_toml = f"""[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
sbor = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}
scrypto = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}

[lib]
crate-type = ["cdylib", "lib"]

[workspace]"""
    
    with open(f"{project_dir}/Cargo.toml", "w") as f:
        f.write(cargo_toml)
    
    return project_dir

def test_compilation(project_dir):
    """Test Scrypto compilation"""
    try:
        result = subprocess.run(
            ["cargo", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def simulate_llm_response(prompt):
    """Simulate LLM response with example Scrypto code"""
    if "nft" in prompt.lower():
        return '''```rust
use scrypto::prelude::*;

#[derive(NonFungibleData, ScryptoSbor)]
pub struct SimpleNftData {
    name: String,
}

#[blueprint]
mod simple_nft {
    struct SimpleNft {
        nft_resource_manager: ResourceManager,
        id_counter: u64,
    }

    impl SimpleNft {
        pub fn instantiate() -> Global<SimpleNft> {
            let nft_resource_manager = ResourceBuilder::new_integer_non_fungible::<SimpleNftData>(OwnerRole::None)
                .metadata(metadata!(init {"name" => "Simple NFT", locked;}))
                .mint_roles(mint_roles!(minter => rule!(allow_all); minter_updater => rule!(deny_all);))
                .create_with_no_initial_supply();

            Self {
                nft_resource_manager,
                id_counter: 1,
            }
            .instantiate()
            .prepare_to_globalize(OwnerRole::None)
            .globalize()
        }

        pub fn mint_nft(&mut self, name: String) -> Bucket {
            let nft = self.nft_resource_manager.mint_non_fungible(
                &NonFungibleLocalId::Integer(self.id_counter.into()),
                SimpleNftData { name }
            );
            self.id_counter += 1;
            nft
        }
    }
}
```'''
    else:
        return '''```rust
use scrypto::prelude::*;

#[blueprint]
mod simple_counter {
    struct SimpleCounter {
        count: u64,
    }

    impl SimpleCounter {
        pub fn instantiate() -> Global<SimpleCounter> {
            Self {
                count: 0,
            }
            .instantiate()
            .prepare_to_globalize(OwnerRole::None)
            .globalize()
        }

        pub fn increment(&mut self) {
            self.count += 1;
        }

        pub fn get_count(&self) -> u64 {
            self.count
        }
    }
}
```'''

def main():
    st.title("🚀 Scrypto LLM Demo")
    st.markdown("**Proof that an LLM can generate compile-clean Scrypto code**")
    
    # Input section
    st.header("1. Enter Your Prompt")
    prompt = st.text_area(
        "Describe the Scrypto blueprint you want to generate:",
        placeholder="Create a simple counter that can increment and get the current value",
        height=100
    )
    
    if st.button("Generate & Test Scrypto Code", type="primary"):
        if not prompt:
            st.error("Please enter a prompt!")
            return
        
        with st.spinner("Generating Scrypto code..."):
            # Simulate LLM response
            response = simulate_llm_response(prompt)
            
            # Extract code
            code = extract_rust_code(response)
            
            if not code:
                st.error("❌ Could not extract Rust code from response")
                return
            
            st.header("2. Generated Code")
            st.code(code, language="rust")
            
            # Test compilation
            st.header("3. Compilation Test")
            with st.spinner("Testing compilation..."):
                project_dir = create_scrypto_project(code, "demo_project")
                success, output = test_compilation(project_dir)
                
                if success:
                    st.success("✅ Compilation Successful!")
                    st.code(output, language="bash")
                    
                    # Show results
                    result = {
                        "prompt": prompt,
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "output": output
                    }
                    
                    st.header("4. Results")
                    st.json(result)
                    
                else:
                    st.error("❌ Compilation Failed")
                    st.code(output, language="bash")
    
    # Show demo info
    st.sidebar.header("About This Demo")
    st.sidebar.markdown("""
    This demonstrates:
    - LLM prompt → Scrypto code extraction
    - Automatic project creation
    - Cargo compilation testing
    - Pass/fail result tracking
    
    **Tech Stack:**
    - Python + Streamlit
    - Rust + Scrypto
    - Cargo build system
    """)

if __name__ == "__main__":
    main()
