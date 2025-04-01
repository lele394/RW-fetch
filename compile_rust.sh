# Compile it
cd rw_fetch_rs
cargo build --release

# copy bins back
cd ../
cp ./rw_fetch_rs/target/release/rw_fetch_rs ./rw_fetch_rs.o
