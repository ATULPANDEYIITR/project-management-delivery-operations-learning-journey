'use strict';

/*
 * Activity Duration Estimation
 *
 * This Node.js program models task-duration estimation as an event-driven
 * workflow. It demonstrates weighted estimates, historical calibration,
 * duration distributions, asynchronous task completion, dependency handling,
 * and estimation-quality measurement.
 */

class DurationEstimate {
  constructor(optimistic, mostLikely, pessimistic) {
    if (![optimistic, mostLikely, pessimistic].every(Number.isFinite)) {
      throw new TypeError('All durations must be finite numbers.');
    }

    if (optimistic < 0 || mostLikely < 0 || pessimistic < 0) {
      throw new RangeError('Durations cannot be negative.');
    }

    if (!(optimistic <= mostLikely && mostLikely <= pessimistic)) {
      throw new RangeError(
        'Expected optimistic <= mostLikely <= pessimistic.'
      );
    }

    this.optimistic = optimistic;
    this.mostLikely = mostLikely;
    this.pessimistic = pessimistic;
  }

  get pert() {
    return (
      this.optimistic +
      4 * this.mostLikely +
      this.pessimistic
    ) / 6;
  }

  get uncertainty() {
    return (this.pessimistic - this.optimistic) / 6;
  }
}

class Activity {
  constructor(name, type, estimate, dependencies = []) {
    if (!name.trim()) {
      throw new Error('Activity name cannot be empty.');
    }

    this.name = name;
    this.type = type;
    this.estimate = estimate;
    this.dependencies = [...dependencies];
  }
}

class ActivityEvent {
  constructor(type, activity, timestamp) {
    this.type = type;
    this.activity = activity;
    this.timestamp = timestamp;
  }
}

class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(eventType, listener) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }

    this.listeners.get(eventType).push(listener);
  }

  emit(eventType, event) {
    const listeners = this.listeners.get(eventType) ?? [];

    for (const listener of listeners) {
      listener(event);
    }
  }
}

function heading(title) {
  console.log(`\n${'='.repeat(76)}`);
  console.log(title);
  console.log('='.repeat(76));
}

function estimateWithSimpleAverage(estimate) {
  return (
    estimate.optimistic +
    estimate.mostLikely +
    estimate.pessimistic
  ) / 3;
}

function demonstrateWeightedEstimation() {
  heading('Weighted Activity Duration Estimation');

  const estimate = new DurationEstimate(4, 9, 20);

  console.log(`Optimistic : ${estimate.optimistic.toFixed(2)} h`);
  console.log(`Most likely: ${estimate.mostLikely.toFixed(2)} h`);
  console.log(`Pessimistic: ${estimate.pessimistic.toFixed(2)} h`);
  console.log(`Simple mean: ${estimateWithSimpleAverage(estimate).toFixed(2)} h`);
  console.log(`PERT       : ${estimate.pert.toFixed(2)} h`);
  console.log(`Uncertainty: ${estimate.uncertainty.toFixed(2)} h`);
}

const historicalActivities = [
  { type: 'analysis', estimated: 6, actual: 8 },
  { type: 'analysis', estimated: 10, actual: 11 },
  { type: 'implementation', estimated: 12, actual: 18 },
  { type: 'implementation', estimated: 20, actual: 23 },
  { type: 'testing', estimated: 10, actual: 9 },
  { type: 'testing', estimated: 14, actual: 17 },
  { type: 'integration', estimated: 8, actual: 12 },
  { type: 'integration', estimated: 15, actual: 18 }
];

function calculateCalibrationFactor(records) {
  const estimated = records.reduce((sum, row) => sum + row.estimated, 0);
  const actual = records.reduce((sum, row) => sum + row.actual, 0);

  if (estimated <= 0) {
    throw new Error('Historical estimated duration must be positive.');
  }

  return actual / estimated;
}

function calculateTypeCalibration(records) {
  const groups = new Map();

  for (const record of records) {
    if (!groups.has(record.type)) {
      groups.set(record.type, []);
    }

    groups.get(record.type).push(record);
  }

  const factors = new Map();

  for (const [type, group] of groups) {
    const estimated = group.reduce(
      (sum, row) => sum + row.estimated,
      0
    );
    const actual = group.reduce(
      (sum, row) => sum + row.actual,
      0
    );

    factors.set(type, actual / estimated);
  }

  return factors;
}

function demonstrateHistoricalCalibration() {
  heading('Historical Calibration');

  const globalFactor = calculateCalibrationFactor(historicalActivities);
  const typeFactors = calculateTypeCalibration(historicalActivities);

  console.log(`Global actual/estimated factor: ${globalFactor.toFixed(3)}`);

  for (const [type, factor] of typeFactors) {
    console.log(`${type.padEnd(16)} ${factor.toFixed(3)}`);
  }

  const estimate = new DurationEstimate(8, 12, 20);
  const raw = estimate.pert;
  const calibrated = raw * typeFactors.get('implementation');

  console.log(`\nRaw implementation estimate: ${raw.toFixed(2)} h`);
  console.log(`Calibrated estimate         : ${calibrated.toFixed(2)} h`);
}

function createSeededRandom(seed) {
  let state = seed >>> 0;

  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function triangularRandom(estimate, random) {
  const u = random();
  const range = estimate.pessimistic - estimate.optimistic;

  if (range === 0) {
    return estimate.optimistic;
  }

  const modePosition =
    (estimate.mostLikely - estimate.optimistic) / range;

  if (u < modePosition) {
    return estimate.optimistic +
      Math.sqrt(
        u * range * (estimate.mostLikely - estimate.optimistic)
      );
  }

  return estimate.pessimistic -
    Math.sqrt(
      (1 - u) * range * (estimate.pessimistic - estimate.mostLikely)
    );
}

function percentile(values, percentage) {
  if (!values.length) {
    throw new Error('Cannot calculate a percentile from empty data.');
  }

  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * percentage / 100;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);

  if (lower === upper) {
    return sorted[lower];
  }

  const fraction = index - lower;

  return sorted[lower] +
    (sorted[upper] - sorted[lower]) * fraction;
}

function simulateActivity(estimate, simulations = 10000, seed = 123) {
  if (!Number.isInteger(simulations) || simulations <= 0) {
    throw new RangeError('Simulation count must be a positive integer.');
  }

  const random = createSeededRandom(seed);
  const values = [];

  for (let i = 0; i < simulations; i += 1) {
    values.push(triangularRandom(estimate, random));
  }

  return values;
}

function demonstrateSimulation() {
  heading('Probabilistic Activity Duration');

  const estimate = new DurationEstimate(5, 10, 24);
  const results = simulateActivity(estimate);

  console.log(`Mean       : ${
    results.reduce((a, b) => a + b, 0) / results.length
  }.toFixed(2) h`);

  console.log(`Median     : ${percentile(results, 50).toFixed(2)} h`);
  console.log(`80th       : ${percentile(results, 80).toFixed(2)} h`);
  console.log(`90th       : ${percentile(results, 90).toFixed(2)} h`);
  console.log(`95th       : ${percentile(results, 95).toFixed(2)} h`);
}

function dependencyOrder(activities) {
  const byName = new Map(activities.map(activity => [activity.name, activity]));
  const state = new Map();
  const ordered = [];

  function visit(name) {
    const current = state.get(name) ?? 0;

    if (current === 1) {
      throw new Error(`Circular dependency involving "${name}".`);
    }

    if (current === 2) {
      return;
    }

    const activity = byName.get(name);

    if (!activity) {
      throw new Error(`Unknown dependency "${name}".`);
    }

    state.set(name, 1);

    for (const dependency of activity.dependencies) {
      visit(dependency);
    }

    state.set(name, 2);
    ordered.push(activity);
  }

  for (const activity of activities) {
    visit(activity.name);
  }

  return ordered;
}

function calculateParallelProjectDuration(activities) {
  const ordered = dependencyOrder(activities);
  const finishTimes = new Map();

  for (const activity of ordered) {
    let start = 0;

    for (const dependency of activity.dependencies) {
      start = Math.max(start, finishTimes.get(dependency));
    }

    finishTimes.set(
      activity.name,
      start + activity.estimate.pert
    );
  }

  return Math.max(...finishTimes.values());
}

function demonstrateDependencyGraph() {
  heading('Dependency-Aware Elapsed Duration');

  const activities = [
    new Activity(
      'Requirements',
      'analysis',
      new DurationEstimate(3, 5, 8)
    ),
    new Activity(
      'Backend',
      'implementation',
      new DurationEstimate(10, 15, 24),
      ['Requirements']
    ),
    new Activity(
      'Frontend',
      'implementation',
      new DurationEstimate(8, 13, 22),
      ['Requirements']
    ),
    new Activity(
      'Backend tests',
      'testing',
      new DurationEstimate(5, 8, 14),
      ['Backend']
    ),
    new Activity(
      'Frontend tests',
      'testing',
      new DurationEstimate(4, 7, 12),
      ['Frontend']
    ),
    new Activity(
      'Integration',
      'integration',
      new DurationEstimate(5, 9, 16),
      ['Backend tests', 'Frontend tests']
    )
  ];

  console.log(
    `Expected elapsed project duration: ${
      calculateParallelProjectDuration(activities).toFixed(2)
    } h`
  );
}

function wait(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function executeActivity(activity, eventBus, scale = 20) {
  eventBus.emit(
    'started',
    new ActivityEvent('started', activity, Date.now())
  );

  const simulatedMilliseconds =
    Math.max(1, Math.round(activity.estimate.pert * scale));

  await wait(simulatedMilliseconds);

  eventBus.emit(
    'completed',
    new ActivityEvent('completed', activity, Date.now())
  );

  return activity.estimate.pert;
}

async function runParallelActivities() {
  heading('Asynchronous Activity Execution');

  const eventBus = new EventBus();

  eventBus.on('started', event => {
    console.log(`START   ${event.activity.name}`);
  });

  eventBus.on('completed', event => {
    console.log(`FINISH  ${event.activity.name}`);
  });

  const activities = [
    new Activity(
      'Schema analysis',
      'analysis',
      new DurationEstimate(2, 4, 7)
    ),
    new Activity(
      'Test design',
      'testing',
      new DurationEstimate(3, 5, 8)
    ),
    new Activity(
      'Documentation',
      'documentation',
      new DurationEstimate(2, 3, 5)
    )
  ];

  const startedAt = Date.now();

  await Promise.all(
    activities.map(activity =>
      executeActivity(activity, eventBus)
    )
  );

  const elapsed = Date.now() - startedAt;

  console.log(`Concurrent wall-clock simulation: ${elapsed} ms`);
  console.log(
    'Promise.all models independent activities occurring concurrently.'
  );
}

function estimationMetrics(planned, actual) {
  if (
    planned.length === 0 ||
    planned.length !== actual.length
  ) {
    throw new Error(
      'Planned and actual arrays must have equal non-zero length.'
    );
  }

  const errors = planned.map(
    (value, index) => actual[index] - value
  );

  const absoluteErrors = errors.map(Math.abs);
  const percentageErrors = planned
    .map((value, index) => value > 0
      ? Math.abs(actual[index] - value) / value
      : null)
    .filter(value => value !== null);

  return {
    mae: absoluteErrors.reduce((a, b) => a + b, 0) /
      absoluteErrors.length,
    mape: (
      percentageErrors.reduce((a, b) => a + b, 0) /
      percentageErrors.length
    ) * 100,
    bias: errors.reduce((a, b) => a + b, 0) / errors.length
  };
}

function demonstrateQualityMeasurement() {
  heading('Estimation Quality');

  const planned = [6, 10, 15, 12, 20];
  const actual = [8, 9, 19, 14, 23];

  const metrics = estimationMetrics(planned, actual);

  console.log(`Mean absolute error: ${metrics.mae.toFixed(2)} h`);
  console.log(`MAPE               : ${metrics.mape.toFixed(2)}%`);
  console.log(`Signed bias         : ${metrics.bias.toFixed(2)} h`);

  if (metrics.bias > 0) {
    console.log('Observed pattern: estimates are biased low.');
  } else if (metrics.bias < 0) {
    console.log('Observed pattern: estimates are biased high.');
  }
}

function demonstrateValidation() {
  heading('Validation and Failure Conditions');

  try {
    new DurationEstimate(10, 6, 15);
  } catch (error) {
    console.log(`Invalid ordering rejected: ${error.message}`);
  }

  try {
    new DurationEstimate(-2, 5, 10);
  } catch (error) {
    console.log(`Negative duration rejected: ${error.message}`);
  }

  try {
    dependencyOrder([
      new Activity(
        'A',
        'implementation',
        new DurationEstimate(1, 2, 3),
        ['B']
      ),
      new Activity(
        'B',
        'testing',
        new DurationEstimate(1, 2, 3),
        ['A']
      )
    ]);
  } catch (error) {
    console.log(`Circular dependency rejected: ${error.message}`);
  }
}

async function main() {
  demonstrateWeightedEstimation();
  demonstrateHistoricalCalibration();
  demonstrateSimulation();
  demonstrateDependencyGraph();
  await runParallelActivities();
  demonstrateQualityMeasurement();
  demonstrateValidation();

  heading('Implementation Boundaries');

  console.log(
    'An effort estimate measures work duration under an assumed working rate;'
  );
  console.log(
    'elapsed duration also depends on dependencies and concurrency.'
  );
  console.log(
    'A probabilistic estimate is preferable when uncertainty is material.'
  );
  console.log(
    'Historical calibration is useful only when past tasks are sufficiently'
  );
  console.log(
    'comparable to the activity being estimated.'
  );
}

main().catch(error => {
  console.error(`Execution failed: ${error.message}`);
  process.exitCode = 1;
});
