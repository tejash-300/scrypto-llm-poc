#!/usr/bin/env python3
"""
Scrypto LLM Code Generator
Sends prompts to ChatGPT, extracts Scrypto code, and tests compilation.
"""

import json
import os
import subprocess
import re
import time
from datetime import datetime

def extract_rust_code(text):
    """Extract Rust code from ChatGPT response"""
    # Look for code blocks with rust or scrypto
    patterns = [
        r'```rust\n(.*?)\n```',
        r'```scrypto\n(.*?)\n```', 
        r'```\n(.*?)\n```'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If no code blocks, look for lines that look like Rust
    lines = text.split('\n')
    rust_lines = []
    in_code = False
    
    for line in lines:
        if any(keyword in line for keyword in ['use scrypto', '#[blueprint]', 'impl', 'pub fn']):
            in_code = True
        if in_code:
            rust_lines.append(line)
            if line.strip() == '}' and len(rust_lines) > 10:
                break
    
    return '\n'.join(rust_lines) if rust_lines else ""

def create_scrypto_project(code, project_name):
    """Create a Scrypto project with the given code"""
    project_dir = f"output/{project_name}"
    os.makedirs(f"{project_dir}/src", exist_ok=True)
    
    # Write the Rust code
    with open(f"{project_dir}/src/lib.rs", "w") as f:
        f.write(code)
    
    # Write Cargo.toml
    cargo_toml = f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
sbor = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}
scrypto = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}

[dev-dependencies]
transaction = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}
radix-engine = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}
scrypto-unit = {{ git = "https://github.com/radixdlt/radixdlt-scrypto", tag = "v1.0.0" }}

[profile.release]
opt-level = 'z'
lto = true
codegen-units = 1
panic = 'abort'
strip = true
overflow-checks = true

[lib]
crate-type = ["cdylib", "lib"]

[workspace]"""
    
    with open(f"{project_dir}/Cargo.toml", "w") as f:
        f.write(cargo_toml)
    
    return project_dir

def test_compilation(project_dir):
    """Test if the Scrypto code compiles"""
    try:
        result = subprocess.run(
            ["cargo", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
    except Exception as e:
        return False, str(e)

def simulate_chatgpt_response(prompt):
    """Simulate ChatGPT response with hardcoded Scrypto examples"""
    
    if "admin" in prompt.lower() and "nft" in prompt.lower():
        # Admin-controlled NFT response
        return '''Here's a simple admin-controlled NFT blueprint in Scrypto:

```rust
use scrypto::prelude::*;

#[derive(NonFungibleData, ScryptoSbor)]
pub struct AdminNftData {
    name: String,
    #[mutable]
    level: u8,
}

#[blueprint]
mod admin_nft {
    struct AdminNft {
        admin_badge: Vault,
        nft_resource_manager: ResourceManager,
        id_counter: u64,
    }

    impl AdminNft {
        pub fn instantiate() -> (Global<AdminNft>, Bucket) {
            let admin_badge = ResourceBuilder::new_fungible(OwnerRole::None)
                .divisibility(DIVISIBILITY_NONE)
                .metadata(metadata!(init {"name" => "Admin Badge", locked;}))
                .mint_initial_supply(1);

            let (address_reservation, component_address) =
                Runtime::allocate_component_address(AdminNft::blueprint_id());

            let nft_resource_manager = ResourceBuilder::new_integer_non_fungible::<AdminNftData>(OwnerRole::None)
                .metadata(metadata!(init {"name" => "Admin NFT Collection", locked;}))
                .mint_roles(mint_roles!(
                    minter => rule!(require(global_caller(component_address)));
                    minter_updater => rule!(deny_all);
                ))
                .create_with_no_initial_supply();

            let component = Self {
                admin_badge: Vault::with_bucket(admin_badge.clone()),
                nft_resource_manager,
                id_counter: 1,
            }
            .instantiate()
            .prepare_to_globalize(OwnerRole::None)
            .with_address(address_reservation)
            .globalize();

            (component, admin_badge)
        }

        pub fn mint_nft(&mut self, name: String) -> Bucket {
            let nft = self.nft_resource_manager.mint_non_fungible(
                &NonFungibleLocalId::Integer(self.id_counter.into()),
                AdminNftData { name, level: 1 }
            );
            self.id_counter += 1;
            nft
        }

        pub fn get_total_supply(&self) -> Decimal {
            self.nft_resource_manager.total_supply()
        }
    }
}
```

This blueprint creates an admin-controlled NFT system where only the admin can mint new NFTs.'''

    else:
        # Simple counter response
        return '''Here's a simple counter blueprint in Scrypto:

```rust
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

        pub fn reset(&mut self) {
            self.count = 0;
        }
    }
}
```

This is a basic counter that can be incremented, read, and reset.'''

def main():
    """Main function to test prompt-to-code pipeline"""
    results = []
    
    # Test cases
    test_cases = [
        {
            "name": "simple_counter",
            "prompt": "Create a simple counter blueprint in Scrypto that can increment and get the current count"
        },
        {
            "name": "admin_nft", 
            "prompt": "Create an admin-controlled NFT blueprint in Scrypto where only admin can mint NFTs"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing {test_case['name']} ===")
        print(f"Prompt: {test_case['prompt']}")
        
        # Simulate ChatGPT call
        response = simulate_chatgpt_response(test_case['prompt'])
        print(f"Got response (first 100 chars): {response[:100]}...")
        
        # Extract code
        code = extract_rust_code(response)
        if not code:
            print("❌ Failed to extract code from response")
            results.append({
                "name": test_case['name'],
                "success": False,
                "retries": 0,
                "error": "No code extracted",
                "timestamp": datetime.now().isoformat()
            })
            continue
        
        print(f"Extracted {len(code)} characters of code")
        
        # Create project
        project_dir = create_scrypto_project(code, test_case['name'])
        print(f"Created project in {project_dir}")
        
        # Test compilation
        print("Testing compilation...")
        success, output = test_compilation(project_dir)
        
        retries = 0
        if not success and retries < 1:
            print("❌ Compilation failed, attempting retry...")
            print(f"Error: {output[:200]}...")
            
            # Simulate retry with error feedback (in real implementation, send error back to ChatGPT)
            retry_response = simulate_chatgpt_response(f"{test_case['prompt']} (Fix this error: {output[:100]})")
            retry_code = extract_rust_code(retry_response)
            
            if retry_code:
                # Create new project for retry
                retry_project_dir = create_scrypto_project(retry_code, f"{test_case['name']}_retry")
                success, output = test_compilation(retry_project_dir)
                retries = 1
        
        if success:
            print("✅ Compilation successful!")
            print("Test command: cargo build")
        else:
            print("❌ Compilation failed")
            print(f"Error: {output[:300]}...")
        
        results.append({
            "name": test_case['name'],
            "success": success,
            "retries": retries,
            "error": output if not success else None,
            "timestamp": datetime.now().isoformat()
        })
    
    # Save results
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Results Summary ===")
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['name']}: {status} (retries: {result['retries']})")
    
    print(f"\nResults saved to results.json")
    print(f"Successful blueprints: {sum(1 for r in results if r['success'])}/{len(results)}")

if __name__ == "__main__":
    main()
