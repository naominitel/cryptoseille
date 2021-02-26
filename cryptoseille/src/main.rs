use std::env;
use std::fs::File;
use std::io::Read;

use chrono::{Local, TimeZone};

fn main() -> std::io::Result<()> {
    let mut datafile = match &env::args().collect::<Vec<_>>()[..] {
        [ _, path ] => File::open(path)?,
        _ => panic!("requires data file as arg")
    };

    let mut contents = String::new();
    datafile.read_to_string(&mut contents)?;
    let data = json::parse(&contents).unwrap();

    let mut bars = Vec::with_capacity(data.len());
    for bar in data.members() {
        // close - open
        let close = bar[4].as_str().unwrap().parse::<f64>().unwrap();
        let open = bar[1].as_str().unwrap().parse::<f64>().unwrap();
        let diff = (close - open) / open * 100.;
        let timestamp = Local.timestamp(bar[0].as_i64().unwrap() / 1000, 0);
        bars.push((diff, timestamp));

        println!("{}: {:+}", timestamp.format("%Y-%m-%d %H:%M"), diff);
    }

    let mut max = bars[0].0;
    let mut min = bars[0].0;
    let mut max_time = bars[0].1;
    let mut min_time = bars[0].1;

    for &(bar, time) in &bars {
        if bar.abs() > max.abs() {
            max = bar;
            max_time = time;
        }
        if bar.abs() < min.abs() && bar != 0. {
            min = bar;
            min_time = time;
        }
    }

    let max_log = max.abs().log2();
    let min_log = min.abs().log2();

    println!("max delta: {:+} at {}", max, max_time.format("%Y-%m-%d %H:%M"));
    println!("min delta: {:+} at {}", min, min_time.format("%Y-%m-%d %H:%M"));

    println!("max log: {:+}", max_log);
    println!("min log: {:+}", min_log);

    // - 2.7    ->      -3       ->       -4
    // - 2.2
    //
    // 1 margin class both sides
    let min_log = min_log.floor() as i64;
    let max_log = max_log.ceil() as i64;
    let nclasses = max_log - min_log;
    let mut val_classes = vec![0 ; nclasses as usize * 2];

    for &(bar, time) in &bars {
        let log = if bar == 0. { min_log } else { bar.abs().log2().floor() as i64 };
        let class = if bar < 0. { log - min_log } else { log - min_log + nclasses };
        println!("bar = {}, log = {}, class = [{} ; {}], classno = {}",
                 bar, bar.abs().log2(), log, log + 1, class);
        val_classes[class as usize] += 1;
    }

    for (i, class) in val_classes.iter().enumerate() {
        let sign = if i < val_classes.len() / 2 { "-" } else { "+" };
        let i = if i >= val_classes.len() / 2 { i - val_classes.len() / 2 } else { i };
        println!("class {} {} [{} ; {}]: {} values", sign, i, min_log + i as i64, min_log + i as i64 + 1, class);
    }

    use hmmm::HMM;
    use ndarray::{array, Array1};
    use rand::SeedableRng as _;
    use rand::rngs::StdRng;

    let data = bars.iter().map(|&(bar, time)| {
        let log = if bar == 0. { min_log } else { bar.abs().log2().floor() as i64 };
        let class = if bar < 0. { log - min_log } else { log - min_log + nclasses };
        class as usize
    }).collect::<Vec<_>>();

    let (training_data, test_data) = data.split_at(2000);

    let mut rng = StdRng::seed_from_u64(1337);
    let hmm = HMM::train(&training_data.iter().map(|&x| x).collect::<Array1<_>>(), 10, val_classes.len(), &mut rng);

    // test
    let mut predictions = hmm.filter(test_data.iter().map(|&x| x));
    let mut iter = test_data.iter().map(|&x| x);
    let mut obs = iter.next().unwrap();

    for _ in 0 .. 100 {
        let p_states = predictions.next().unwrap().p_states;
        
        // probabilities for next state:
        let trans_probs = p_states.dot(&hmm.a);

        // probabilities for next observation:
        let obs_probs = trans_probs.dot(&hmm.b);

        let mut max = 0;
        let mut max_prob = 0.;
        for i in 0 .. hmm.k() {
            if obs_probs[i] >= max_prob {
                max_prob = obs_probs[i];
                max = i;
            }
        }
        println!(" best next obs: {} (prob: {})", max, max_prob);
        obs = iter.next().unwrap();
        println!("=== observing market: {} (prob is: {})", obs, obs_probs[obs]);
    }

    Ok(())
}
