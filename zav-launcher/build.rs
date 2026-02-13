fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_default() == "windows" {
        let mut res = winres::WindowsResource::new();
        res.set_icon("assets/icon.ico");
        res.set("ProductName", "ZAV Hospital System");
        res.set("FileDescription", "ZAV Hospital System Launcher");
        res.set("CompanyName", "Zav Hospital");
        res.set("LegalCopyright", "2026 Zav Hospital");
        res.compile().expect("Failed to compile Windows resources");
    }
}
