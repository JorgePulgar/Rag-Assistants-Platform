import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { assistantsApi } from '@/api/client';
import type { Assistant } from '@/lib/types';
import { toast } from 'sonner';

interface AssistantFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (assistant: Assistant) => void;
  initialValues?: Assistant;
}

export function AssistantForm({
  open,
  onOpenChange,
  onSuccess,
  initialValues,
}: AssistantFormProps) {
  const [name, setName] = useState('');
  const [instructions, setInstructions] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEdit = !!initialValues;

  useEffect(() => {
    if (open) {
      setName(initialValues?.name ?? '');
      setInstructions(initialValues?.instructions ?? '');
      setDescription(initialValues?.description ?? '');
      setErrors({});
    }
  }, [open, initialValues]);

  function validate(): Record<string, string> {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Name is required';
    if (!instructions.trim()) errs.instructions = 'Instructions are required';
    return errs;
  }

  async function handleSubmit() {
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        name: name.trim(),
        instructions: instructions.trim(),
        description: description.trim() || undefined,
      };
      const assistant = isEdit && initialValues
        ? await assistantsApi.update(initialValues.id, payload)
        : await assistantsApi.create(payload);
      onSuccess(assistant);
    } catch {
      toast.error(isEdit ? 'Failed to update assistant' : 'Failed to create assistant');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit assistant' : 'New assistant'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the assistant details below.'
              : 'Configure a new assistant with its instructions.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <div>
            <label
              htmlFor="af-name"
              className="text-xs font-medium text-neutral-700 dark:text-neutral-300"
            >
              Name
            </label>
            <Input
              id="af-name"
              className="mt-1"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Legal Expert"
            />
            {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name}</p>}
          </div>

          <div>
            <label
              htmlFor="af-description"
              className="text-xs font-medium text-neutral-700 dark:text-neutral-300"
            >
              Description
            </label>
            <Input
              id="af-description"
              className="mt-1"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional — shown as subtitle"
            />
          </div>

          <div>
            <label
              htmlFor="af-instructions"
              className="text-xs font-medium text-neutral-700 dark:text-neutral-300"
            >
              Instructions
            </label>
            <Textarea
              id="af-instructions"
              className="mt-1 font-mono text-xs min-h-[120px]"
              value={instructions}
              onChange={e => setInstructions(e.target.value)}
              placeholder="You are a specialist in…"
            />
            {errors.instructions && (
              <p className="text-xs text-red-600 mt-1">{errors.instructions}</p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={() => void handleSubmit()} disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : isEdit ? 'Save changes' : 'Create assistant'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
