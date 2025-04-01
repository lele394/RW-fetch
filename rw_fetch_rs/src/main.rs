// src/main.rs
mod config;
mod sysinfo_fetchers;

use colored::*;
use lazy_static::lazy_static;
use rand::seq::SliceRandom;
use regex::Regex;
use serde::Deserialize;
use std::{
    collections::HashMap,
    env, fs, path::PathBuf,
    sync::mpsc, // Import channels
    thread,    // Keep for thread::sleep maybe, or if needed elsewhere
};
use sysinfo::System;
use threadpool::ThreadPool; // Import threadpool

use config::FetcherType;

#[derive(Deserialize, Debug, Clone)]
struct CacheEntry {
    ansi_art: String,
    category: String,
    #[serde(default)]
    num_lines: usize,
}

type Cache = HashMap<String, CacheEntry>;

// Result type sent back from worker threads: (original_index, result_lines)
type FetchResult = (usize, Vec<String>);

lazy_static! {
    static ref SYS: System = {
        let mut s = System::new_all();
        s.refresh_all();
        s
    };
    static ref ANSI_REGEX: Regex = Regex::new(r"\x1b\[[0-9;?]*[a-zA-Z]").unwrap();
}

fn load_cache(cache_path: &PathBuf) -> Result<Cache, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(cache_path)?;
    if content.trim().is_empty() {
        return Ok(HashMap::new());
    }
    let cache: Cache = serde_json::from_str(&content)?;
    Ok(cache)
}

fn get_visible_width(line: &str) -> usize {
    ANSI_REGEX.replace_all(line, "").chars().count()
}

fn display_art_and_info(ansi_art: &str, sys_info_lines: &[String]) {
    let art_lines: Vec<&str> = ansi_art.lines().collect();
    let max_art_width = art_lines
        .iter()
        .map(|line| get_visible_width(line))
        .max()
        .unwrap_or(0);

    let num_art_lines = art_lines.len();
    let num_info_lines = sys_info_lines.len();
    let max_lines = num_art_lines.max(num_info_lines);

    for i in 0..max_lines {
        let art_line = art_lines.get(i).copied().unwrap_or("");
        let info_line = sys_info_lines.get(i).map(|s| s.as_str()).unwrap_or("");

        let current_art_width = get_visible_width(art_line);
        let padding_needed = max_art_width.saturating_sub(current_art_width);
        let padding = " ".repeat(padding_needed);

        print!("{}", art_line);
        print!("{}", padding);

        if !info_line.is_empty() {
            print!("{}{}", config::IMAGE_INFO_SEPARATOR, info_line);
        }
        println!();
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // --- Configuration & Cache Loading ---
    let exe_path = env::current_exe()?;
    let base_dir = exe_path
        .parent()
        .ok_or("Could not get executable directory")?;
    let cache_path = base_dir.join(config::CACHE_FILE_NAME);

    let cache = match load_cache(&cache_path) {
        Ok(c) => c,
        Err(e) => {
            eprintln!( /* ... error loading cache ... */ );
            return Err(e);
        }
    };

    if cache.is_empty() {
        eprintln!( /* ... cache is empty ... */ );
        return Ok(());
    }

    // --- Filter & Random Selection ---
    let small_entries: Vec<&CacheEntry> = cache
        .values()
        .filter(|entry| entry.category == "small")
        .collect();

    if small_entries.is_empty() {
        eprintln!( /* ... no small entries ... */ );
        return Ok(());
    }

    let mut rng = rand::thread_rng();
    let chosen_entry = small_entries
        .choose(&mut rng)
        .ok_or("Failed to choose a random entry")?;

    // --- Calculate Max Label Width ---
    let max_label_len = config::SYSTEM_INFO_ORDER
        .iter()
        .filter(|item| {
            matches!(
                item.fetcher_type,
                FetcherType::SysinfoFn(_) | FetcherType::ShellCommand(_)
            )
        })
        .map(|item| item.label.len())
        .max()
        .unwrap_or(0);

    // --- Fetch System Info using Thread Pool ---
    let sys_info_lines = {
        let pool = ThreadPool::new(config::MAX_FETCH_THREADS);
        let (tx, rx) = mpsc::channel::<FetchResult>(); // Channel for results

        let num_tasks = config::SYSTEM_INFO_ORDER.len();
        let separator_width = max_label_len + config::SYS_INFO_KV_SEPARATOR.len() + 15; // For separators

        for (index, item) in config::SYSTEM_INFO_ORDER.iter().enumerate() {
            let tx_clone = tx.clone(); // Clone sender for this thread

            // Use static lifetime for item ref to satisfy pool.execute requirement
            // This is safe because SYSTEM_INFO_ORDER is static itself.
            let item_static: &'static config::SysInfoItem = unsafe {
                 // SAFETY: SYSTEM_INFO_ORDER has a static lifetime.
                 std::mem::transmute::<&config::SysInfoItem, &'static config::SysInfoItem>(item)
            };


            pool.execute(move || {
                let result_lines = match item_static.fetcher_type {
                    FetcherType::SysinfoFn(fetcher_fn) => {
                        let value_str = fetcher_fn(&SYS);
                        value_str.lines().map(String::from).collect()
                    }
                    FetcherType::ShellCommand(command_key) => {
                        let value_str = sysinfo_fetchers::fetch_shell_command(command_key);
                        vec![value_str]
                    }
                    FetcherType::Separator(text) => {
                        vec![config::format_separator(text, separator_width)]
                    }
                };
                // Send result back with original index
                tx_clone
                    .send((index, result_lines))
                    .expect("Failed to send result back from thread");
            });
        } // End of task submission loop

        // Drop the original sender. The channel will close when all threads finish
        // and drop their tx_clone senders.
        drop(tx);

        // Collect results from the channel. Order might be arbitrary here.
        let mut collected_results: Vec<FetchResult> = rx.iter().collect();

        // Sort results based on the original index to restore order
        collected_results.sort_by_key(|(index, _)| *index);

        // Format the final lines
        let mut final_formatted_lines = Vec::new();
        for (index, result_lines) in collected_results {
            // Get the corresponding config item again (or use the index directly if needed)
            let item = &config::SYSTEM_INFO_ORDER[index]; // Safe because we collected num_tasks results

             match item.fetcher_type {
                 FetcherType::Separator(_) => {
                    if !result_lines.is_empty() {
                        final_formatted_lines.push(result_lines[0].clone());
                    }
                }
                _ => { // SysinfoFn or ShellCommand
                    if !result_lines.is_empty() {
                        let label_part = config::format_label(
                            &format!("{:<width$}", item.label, width = max_label_len)
                        );
                        final_formatted_lines.push(format!("{}{}", label_part, result_lines[0]));

                        if result_lines.len() > 1 {
                            let indent = " ".repeat(max_label_len + config::SYS_INFO_KV_SEPARATOR.len() + 1);
                            for line in result_lines.iter().skip(1) {
                                final_formatted_lines.push(format!("{}{}", indent, line));
                            }
                        }
                    } else {
                         let label_part = config::format_label(
                            &format!("{:<width$}", item.label, width = max_label_len)
                        );
                         final_formatted_lines.push(format!("{}{}", label_part, config::format_error("N/A")));
                    }
                }
            }
        }
        final_formatted_lines
    }; // Assign the formatted lines

    // --- Display ---
    display_art_and_info(&chosen_entry.ansi_art, &sys_info_lines);

    Ok(())
}