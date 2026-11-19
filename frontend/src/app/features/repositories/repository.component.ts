import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { RepositoryService } from '../../core/services/repository.service';

@Component({ standalone: true, imports: [CommonModule], template: `
<div class="explorer">
  <aside>
    <h2>Explorer</h2>
    <p class="error" *ngIf="error()">{{ error() }}</p>
    <p *ngIf="loadingFiles()">Loading files...</p>
    <button *ngFor="let file of files()" (click)="openFile(file)">{{ file.type === 'dir' ? '📁 ' : '' }}{{ file.name }}</button>
  </aside>
  <main><h2>{{ selectedPath() || 'Repository' }}</h2><pre>{{ content() }}</pre></main>
</div>` })
export class RepositoryComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(RepositoryService);
  readonly files = signal<any[]>([]);
  readonly content = signal('Select a file');
  readonly selectedPath = signal('');
  readonly loadingFiles = signal(true);
  readonly error = signal('');
  private loadId = 0;

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadId = id;
    this.service.files(id).subscribe({
      next: data => {
        const normalized = Array.isArray(data) ? data : data.result;
        this.files.set(Array.isArray(normalized) ? normalized : []);
        this.loadingFiles.set(false);
      },
      error: error => {
        this.error.set(error.error?.detail || 'Unable to load repository files.');
        this.loadingFiles.set(false);
      }
    });
  }

  openFile(file: any) {
    if (file.type === 'dir') {
      this.loadDirectory(file.path);
      return;
    }

    this.selectedPath.set(file.path);
    this.content.set('Loading...');
    this.error.set('');
    this.service.fileContent(this.loadId, file.path).subscribe({
      next: data => {
        const normalized = data && !Array.isArray(data) && 'result' in data ? data.result : data;
        this.content.set(normalized?.content || '');
      },
      error: error => this.error.set(error.error?.detail || 'Unable to load file content.')
    });
  }

  private loadDirectory(path: string) {
    this.loadingFiles.set(true);
    this.error.set('');
    this.selectedPath.set(path);
    this.service.files(this.loadId, path).subscribe({
      next: data => {
        const normalized = Array.isArray(data) ? data : data.result;
        this.files.set(Array.isArray(normalized) ? normalized : []);
        this.loadingFiles.set(false);
      },
      error: error => {
        this.error.set(error.error?.detail || 'Unable to load directory.');
        this.loadingFiles.set(false);
      }
    });
  }
}
