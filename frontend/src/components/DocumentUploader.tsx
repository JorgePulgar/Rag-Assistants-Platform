import { useRef, useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { documentsApi } from '@/api/client';
import { toast } from 'sonner';

interface DocumentUploaderProps {
  assistantId: string;
  onUploaded: () => void;
}

export function DocumentUploader({ assistantId, onUploaded }: DocumentUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  async function handleFile(file: File) {
    setIsUploading(true);
    try {
      await documentsApi.upload(assistantId, file);
      onUploaded();
      toast.success(`"${file.name}" uploaded`);
    } catch {
      toast.error(`Failed to upload "${file.name}"`);
    } finally {
      setIsUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      void handleFile(file);
      e.target.value = '';
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload document"
      className={[
        'border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors',
        isDragging
          ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20'
          : 'border-neutral-300 dark:border-neutral-700 hover:border-neutral-400 dark:hover:border-neutral-600',
        isUploading ? 'pointer-events-none opacity-60' : '',
      ].join(' ')}
      onClick={() => !isUploading && inputRef.current?.click()}
      onKeyDown={e => e.key === 'Enter' && !isUploading && inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {isUploading ? (
        <Loader2 className="h-6 w-6 text-neutral-400 animate-spin" aria-hidden="true" />
      ) : (
        <Upload className="h-6 w-6 text-neutral-400" aria-hidden="true" />
      )}
      <p className="text-sm text-neutral-600 dark:text-neutral-400 text-center">
        {isUploading ? 'Uploading…' : 'Drop files here or click to upload'}
      </p>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.pptx,.txt"
        onChange={handleChange}
      />
    </div>
  );
}
