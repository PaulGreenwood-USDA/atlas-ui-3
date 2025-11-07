{{/*
Common template helpers
*/}}

{{- define "atlas.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "atlas.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- /* service names */ -}}
{{- define "atlas.svc.main" -}}{{ include "atlas.fullname" . }}-main-app{{- end -}}
{{- define "atlas.svc.auth" -}}{{ include "atlas.fullname" . }}-auth-app{{- end -}}
{{- define "atlas.svc.nginx" -}}{{ include "atlas.fullname" . }}-nginx{{- end -}}
{{- define "atlas.svc.minio" -}}{{ include "atlas.fullname" . }}-minio{{- end -}}

{{- /* selector labels */ -}}
{{- define "atlas.labels" -}}
app.kubernetes.io/name: {{ include "atlas.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
