# Queries

## Ping

```grapqhl
query {
	ping
}
```

## Nodes

```graphql
query {
	nodes {
    id
    virtualization
    interfaces { name }
  }
}
```

## Impairment

```graphql
query {
	impairment(distance: 10) {
    maxConnected
    initial {
      connected
      settings
    }
    requested {
      connected
      settings
    }
  }
}
```

## Impairments

```graphql
query {
  impairments {
    node {
      id
      virtualization
      interface {
        nodeClass
        nodeClassName
        nrHostInterface
        mac
        name
      }
      links {
        node { id }
        interface {name}
        impairment
        connected
      }
    }
  }
}
```

## Distances

```graphql
query {
  distances {
  	node {
      id
      interfaces { name }
      links {
        node { id }
        distance
      }
    }
  }
}
```

