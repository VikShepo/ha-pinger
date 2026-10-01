FROM golang:1.27.1-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /ncc-vpn .
RUN mkdir -p /licenses && find /go/pkg/mod -type f \( -iname 'LICENSE*' -o -iname 'COPYING*' -o -name NOTICE \) -exec sh -c 'for path do relative="${path#/go/pkg/mod/}"; mkdir -p "/licenses/$(dirname "$relative")"; cp "$path" "/licenses/$relative"; done' sh {} + && cp /usr/local/go/LICENSE /licenses/GO-LICENSE

FROM alpine:3.23
RUN apk add --no-cache ca-certificates
COPY --from=build /ncc-vpn /usr/local/bin/ncc-vpn
COPY --from=build /licenses /usr/share/licenses/ncc-vpn
ARG BUILD_VERSION=1.4.1
LABEL io.hass.type="app" io.hass.version="${BUILD_VERSION}" io.hass.arch="aarch64|amd64"
EXPOSE 8099
ENTRYPOINT ["/usr/local/bin/ncc-vpn"]
