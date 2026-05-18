/**
 * Priority queue with retry semantics.
 *
 * Used by the background worker pool to schedule failed jobs for retry.
 * Higher-priority jobs run first; among same-priority jobs, jobs with
 * fewer attempts run first to avoid starving retried-but-not-exhausted
 * jobs.
 */
type Job = { id: string; priority: number; attempts: number; payload: unknown };

class RetryScheduler {
  private queue: Job[] = [];
  private readonly maxAttempts: number;

  constructor(maxAttempts: number = 3) {
    this.maxAttempts = maxAttempts;
  }

  enqueue(job: Job): void {
    if (job.attempts >= this.maxAttempts) {
      throw new Error(`Job ${job.id} exhausted retries`);
    }
    this.queue.push(job);
    this.queue.sort(
      (a, b) => b.priority - a.priority || a.attempts - b.attempts,
    );
  }

  dequeue(): Job | undefined {
    return this.queue.shift();
  }

  retry(job: Job): void {
    job.attempts += 1;
    this.enqueue(job);
  }

  size(): number {
    return this.queue.length;
  }
}

export { RetryScheduler, Job };
