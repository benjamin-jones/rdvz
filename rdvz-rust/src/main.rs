extern crate rand;

use std::io::{self,BufRead};
use std::io::Write;
use std::io::Read;
use std::io::stdout;
use std::path::Path;
use std::process::Command;
use std::error::Error;
use std::fs::File;
use rand::Rng;

fn raw_input(prompt: &str) -> String {
 
    print!("{}",prompt);

    // Flush the prompt due to lack of newline
    stdout().flush().ok().expect("Could not flush stdout");

    // Acquire input from stdin
    let mut line = String::new();
    let stdin = io::stdin();

    stdin.lock().read_line(&mut line).unwrap();

    // Return line to caller
    return line.trim().to_string();
}

fn id_generator() -> String {
    return rand::thread_rng().gen_ascii_chars().take(16).collect::<String>();
}

fn path_exists(path: &Path) -> bool {

    println!("Entering path_exists()...");
    match File::open(path) {
        Err(_) => {
            println!("Didn't open file");
            return false;
        },
        Ok(_) => {
            println!("Opened file");
            return true;
        },
    };
}

fn main() {

    println!("RDVZ Online");

    let line: String = raw_input("<Enter> for a new session or enter key: ");    

    let key: String = match &line[..] {
        "" => id_generator(),
        _  => String::from(&line [..])
    };

    if &key[..] != &line[..] {
        println!("Session key: {}", key);
    } else {
        println!("Enterting session {}", key);
    }

    let mut fifo: String = String::new();

    fifo.push_str("/tmp/");
    fifo.push_str(&key[..]);

    println!("Opening fifo {}", fifo);

    let path = Path::new(&fifo[..]);

    if path_exists(path) {
        // We're not first

        println!("Not first");

        let mut file = match File::create(&path) {
            Err(why) => panic!("couldn't open {}: {}", path.display(), Error::description(&why)),
            Ok(file)    => file,
        };

        match file.write_all("1".as_bytes()) {
            Err(why) =>  {
                panic!("couldn't write to {}: {}", path.display(), Error::description(&why))
            },
            Ok(_) => println!("Sent message"),
        }
        
    } else {
        // We're first!

        println!("First");

        // Make FIFO
        Command::new("mkfifo").arg(path.as_os_str()).output().unwrap_or_else(|e| {
                panic!("failed to execute process: {}", e)
            });
        
        let mut file = match File::open(&path) {
            Err(why) => panic!("couldn't open {}: {}", path.display(), Error::description(&why)),
                Ok(file)    => file,
        };

        let mut s = String::new();
        match file.read_to_string(&mut s) {
            Err(why) => panic!("couldn't read {}: {}", path.display(), Error::description(&why)),
            Ok(_)    => println!("Good to go"),
        };
    }

    Command::new("rm").arg(path.as_os_str()).output().unwrap_or_else(|e| {
            panic!("failed to execute process: {}", e)
        });
}

