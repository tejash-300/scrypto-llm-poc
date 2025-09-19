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