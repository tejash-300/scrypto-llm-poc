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