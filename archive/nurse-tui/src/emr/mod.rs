//! EMR integration - Temperature only

mod client;
mod temperature;

pub use client::EmrClient;
pub use temperature::{Patient, Vitals, TemperatureRecord, generate_vitals};
