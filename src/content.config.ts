import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const links = z
  .object({
    poster: z.string().optional(),
    paper: z.string().optional(),
    code: z.string().optional(),
    videos: z.string().optional(),
    slides: z.string().optional(),
    lab: z.string().optional(),
    minilabs: z.string().optional(),
    exercises: z.string().optional(),
  })
  .default({});

const research = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/research' }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    summary: z.string(),
    authors: z.array(z.string()),
    kind: z.enum(['poster', 'paper', 'talk', 'project']),
    venue: z.string().optional(),
    date: z.coerce.date(),
    status: z.string().optional(),
    links,
  }),
});

const teaching = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/teaching' }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    format: z.string(),
    date: z.coerce.date(),
    links,
  }),
});

export const collections = { research, teaching };
