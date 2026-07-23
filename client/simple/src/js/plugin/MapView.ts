// SPDX-License-Identifier: AGPL-3.0-or-later

import "ol/ol.css";
import { Feature, Map as OlMap, View } from "ol";
import { GeoJSON } from "ol/format";
import { Point } from "ol/geom";
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import { fromLonLat } from "ol/proj";
import { OSM, Vector as VectorSource } from "ol/source";
import { Circle, Fill, Stroke, Style } from "ol/style";
import { Plugin } from "../Plugin.ts";

/**
 * Interactive map view for location search results.
 *
 * Displays:
 * - Base layer: OpenStreetMap tile layer
 * - Point marker: Single coordinate location
 * - GeoJSON overlay: Geographic features (if provided)
 *
 * @remarks
 * Uses OpenLayers library for map rendering. Coordinates expected in WGS84 (EPSG:4326).
 */
export default class MapView extends Plugin {
  private static readonly MAX_ZOOM_LEVEL = 16;
  private static readonly MARKER_RADIUS = 6;
  private static readonly MARKER_COLOR = "#3050ff";
  private static readonly GEOJSON_STROKE_WIDTH = 2;
  private static readonly GEOJSON_FILL_COLOR = "#3050ff33"; // Blue with 20% opacity
  private static readonly VIEWPORT_PADDING = [20, 20, 20, 20]; // px: top, right, bottom, left

  private static readonly DATA_ATTRIBUTES = {
    ELEMENT_ID: "leafletTarget",
    LONGITUDE: "mapLon",
    LATITUDE: "mapLat",
    GEOJSON: "mapGeojson"
  } as const;

  private static readonly PROJECTION = {
    DATA: "EPSG:4326",
    MAP: "EPSG:3857"
  } as const;

  private readonly mapElement: HTMLElement;

  public constructor(mapElement: HTMLElement) {
    super("mapView");
    this.mapElement = mapElement;
  }

  protected async run(): Promise<void> {
    try {
      const { coordinates, geojson, targetElement } = this.extractMapData();
      const map = this.createBaseMap(targetElement);

      this.addMarkerLayer(map, coordinates);

      if (geojson) {
        this.addGeoJsonLayer(map, geojson);
      }
    } catch (error) {
      this.handleError("Failed to initialize map", error);
    }
  }

  /**
   * Extracts and parses map configuration from element data attributes.
   *
   * @returns Parsed coordinates, GeoJSON string, and target element ID
   * @throws {Error} If required attributes are missing or invalid
   */
  private extractMapData(): { coordinates: [number, number]; geojson?: string; targetElement: string } {
    const {
      [MapView.DATA_ATTRIBUTES.ELEMENT_ID]: targetElement,
      [MapView.DATA_ATTRIBUTES.LONGITUDE]: lonStr = "0",
      [MapView.DATA_ATTRIBUTES.LATITUDE]: latStr = "0",
      [MapView.DATA_ATTRIBUTES.GEOJSON]: geojson
    } = this.mapElement.dataset;

    if (!targetElement) {
      throw new Error(`Required data attribute '${MapView.DATA_ATTRIBUTES.ELEMENT_ID}' not found`);
    }

    const lon = Number.parseFloat(lonStr);
    const lat = Number.parseFloat(latStr);

    if (Number.isNaN(lon) || Number.isNaN(lat)) {
      throw new Error(`Invalid coordinates: lon=${lonStr}, lat=${latStr}`);
    }

    return { coordinates: [lon, lat], geojson, targetElement };
  }

  /**
   * Creates the base map with OSM tile layer and view configuration.
   *
   * @param targetElementId HTML element ID where map will render
   * @returns Configured OpenLayers Map instance
   */
  private createBaseMap(targetElementId: string): OlMap {
    const view = new View({
      maxZoom: MapView.MAX_ZOOM_LEVEL,
      enableRotation: false
    });

    return new OlMap({
      target: targetElementId,
      layers: [new TileLayer({ source: new OSM({ maxZoom: MapView.MAX_ZOOM_LEVEL }) })],
      view
    });
  }

  /**
   * Adds a marker layer displaying a single point location.
   *
   * @param map OpenLayers map instance
   * @param coordinates [longitude, latitude] in WGS84
   */
  private addMarkerLayer(map: OlMap, [lon, lat]: [number, number]): void {
    const markerSource = new VectorSource({
      features: [
        new Feature({
          geometry: new Point(fromLonLat([lon, lat]))
        })
      ]
    });

    const markerLayer = new VectorLayer({
      source: markerSource,
      style: this.createMarkerStyle()
    });

    map.addLayer(markerLayer);
  }

  /**
   * Creates the visual style for the marker point.
   */
  private createMarkerStyle(): Style {
    return new Style({
      image: new Circle({
        radius: MapView.MARKER_RADIUS,
        fill: new Fill({ color: MapView.MARKER_COLOR })
      })
    });
  }

  /**
   * Adds a GeoJSON feature layer and auto-fits the viewport to its bounds.
   *
   * @param map OpenLayers map instance
   * @param geojsonStr GeoJSON string to parse and display
   */
  private addGeoJsonLayer(map: OlMap, geojsonStr: string): void {
    let geojsonData: unknown;

    try {
      geojsonData = JSON.parse(geojsonStr);
    } catch (error) {
      throw new Error(`Invalid GeoJSON: ${error instanceof Error ? error.message : String(error)}`);
    }

    const geoSource = new VectorSource({
      features: new GeoJSON().readFeatures(geojsonData, {
        dataProjection: MapView.PROJECTION.DATA,
        featureProjection: MapView.PROJECTION.MAP
      })
    });

    const geoLayer = new VectorLayer({
      source: geoSource,
      style: this.createGeoJsonStyle()
    });

    map.addLayer(geoLayer);
    this.fitViewToFeatures(map, geoSource);
  }

  /**
   * Creates the visual style for GeoJSON features.
   */
  private createGeoJsonStyle(): Style {
    return new Style({
      stroke: new Stroke({ color: MapView.MARKER_COLOR, width: MapView.GEOJSON_STROKE_WIDTH }),
      fill: new Fill({ color: MapView.GEOJSON_FILL_COLOR })
    });
  }

  /**
   * Auto-fits the map view to show all GeoJSON features.
   *
   * @param map OpenLayers map instance
   * @param source Vector source containing features
   */
  private fitViewToFeatures(map: OlMap, source: VectorSource): void {
    const extent = source.getExtent();

    if (extent && extent.every(isFinite)) {
      const view = map.getView();
      view.fit(extent, { padding: MapView.VIEWPORT_PADDING });
    }
  }

  /**
   * Logs and handles map initialization errors gracefully.
   *
   * @param message Error context message
   * @param error The error object
   */
  private handleError(message: string, error: unknown): void {
    const errorDetails = error instanceof Error ? error.message : String(error);
    console.error(`${message}: ${errorDetails}`);
  }

  protected async post(): Promise<void> {
    // No post-processing needed for map view
  }
}
